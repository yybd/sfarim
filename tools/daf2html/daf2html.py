#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daf2html — ממיר דף גמרא (PDF וקטורי עטוף ב-js) לדף HTML בצורת הדף המדויקת.

עקרון: חילוץ ברמת התו הבודד מה-PDF, קיבוץ לשורות פיזיות לפי baseline,
ומיקום אבסולוטי של כל שורה. כך צורת הדף זהה למקור ואינה משתנה לעולם —
לכל דף, גם דפים עם מבנה חריג.

שימוש:
    python daf2html.py <masechta_dir_index> <page_index> [--out out.html]
    python daf2html.py --pdf path/to/daf.pdf --out out.html
"""
import argparse
import base64
import json
import re
from pathlib import Path

import pymupdf

try:
    from fontTools.cffLib import CFFFontSet
    from fontTools import agl
    HAVE_FONTTOOLS = True
except ImportError:
    HAVE_FONTTOOLS = False

SHAS_DIR = Path(__file__).resolve().parents[2] / "public" / "shas" / "shas"

# ---------------------------------------------------------------- encodings

HEB = re.compile(r'[א-ת]')
HEB_MARK = re.compile(r'[֑-ׇ]')

# פונט הפסוקים (תורה אור השלם): אותיות רגילות בפריסת SI-960
# (`abcdefghijklmnopqrstuvwxyz -> א..ת עם סופיות בתוך הרצף)
SI960 = {chr(0x60 + i): chr(0x5D0 + i) for i in range(27)}
# אותיות רישיות = הצורות הדגושות/מיוחדות, בסדר אלפביתי רציף.
# מיפוי אמפירי שאומת מול פסוקים בשישה דפים (ברכות, חגיגה ועוד)
SI960.update({
    'A': 'בּ', 'B': 'גּ', 'C': 'דּ', 'D': 'הּ', 'E': 'וּ', 'F': 'וֹ',
    'G': 'זּ', 'H': 'טּ', 'I': 'יּ', 'K': 'ךְ', 'L': 'ךָ', 'M': 'כּ',
    'N': 'לּ', 'O': 'מּ', 'P': 'נּ', 'Q': 'סּ', 'R': 'פּ', 'S': 'צּ',
    'T': 'קּ', 'U': 'שׂ', 'V': 'שּׂ', 'W': 'שׁ', 'X': 'שּׁ', 'Y': 'תּ',
    'õ': 'אַ', 'ô': 'אָ', '÷': 'לֹ',
})

# ניקוד בפונט הפסוקים — נגזר מאותו יישור אמפירי
SI960_MARKS = {
    '§': 'ְ',   # שווא
    '¨': 'ָ',   # קמץ
    '©': 'ַ',   # פתח
    '¦': 'ִ',   # חיריק
    '¥': 'ֵ',   # צירי
    '¤': 'ֶ',   # סגול
    '£': 'ֲ',   # חטף פתח
    '¡': 'ֱ',   # חטף סגול
    'ª': 'ֻ',   # קובוץ
    'Ÿ': 'ֹ',   # חולם
    '±': 'ֳ',   # חטף קמץ
}


def _score_hebrew(s: str) -> float:
    if not s:
        return 0.0
    return len(HEB.findall(s)) / max(1, len(re.sub(r'[\s\d.,:;()\[\]\'"־-]', '', s)))


def decode_latin1_cp1255(t: str) -> str:
    return ''.join(
        bytes([ord(c)]).decode('cp1255') if 0xE0 <= ord(c) <= 0xFA else c
        for c in t)


def decode_macroman_cp1255(t: str) -> str:
    out = []
    for ch in t:
        try:
            d = ch.encode('mac_roman').decode('cp1255')
            out.append(d if HEB.match(d) else ch)
        except (UnicodeEncodeError, UnicodeDecodeError):
            out.append(ch)
    return ''.join(out)


def decode_si960(t: str) -> str:
    return ''.join(SI960.get(c) or SI960_MARKS.get(c, c) for c in t)


DECODERS = {
    'unicode': lambda s: s,
    'latin1': decode_latin1_cp1255,
    'macroman': decode_macroman_cp1255,
    'si960': decode_si960,
    # פונט קישוט: כל גליף בו הוא הקישוט המפריד, יהא קודו אשר יהא
    'ornament': lambda s: ORNAMENT * len(s),
}


def detect_encoding(sample: str) -> str:
    best, best_score = 'unicode', _score_hebrew(sample)
    for name in ('latin1', 'macroman', 'si960'):
        sc = _score_hebrew(DECODERS[name](sample))
        if sc > best_score + 0.05:
            best, best_score = name, sc
    return best


# ---------------------------------------------------------------- extraction

def load_pdf(js_path: Path) -> bytes:
    data = js_path.read_text(errors='replace')
    m = re.search(r'loadedPdfData\("([^"]*)"\)', data, re.S)
    if not m:
        raise ValueError(f"not a loadedPdfData js file: {js_path}")
    return base64.b64decode(m.group(1))


def extract_chars(page, fixmaps):
    """כל תו בודד עם מיקומו, הפונט והגודל שלו."""
    d = page.get_text('rawdict')
    chars = []
    for b in d['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            for s in l['spans']:
                fm = fixmaps.get(s['font'].split('+')[-1], {})
                for c in s['chars']:
                    chars.append({
                        'c': fm.get(c['c'], c['c']),
                        'font': s['font'],
                        'size': s['size'],
                        'bbox': c['bbox'],
                        'oy': c['origin'][1],
                    })
    return chars


# שמות גליפים שאינם ב-AGL ולכן MuPDF פולט עבורם את הקוד הגולמי;
# ממופים לתו שה-AGL היה נותן, כדי שהמפענחים הרגילים יטפלו בהם.
NON_AGL = {'applelogo': ''}
ORNAMENT = '❖'  # קישוט מפריד בין מדורי השוליים
# שמות גליפים שמחוץ ל-AGLFN אך MuPDF מכיר
EXTRA_GLYPH_NAMES = {'threesuperior': '³', 'twosuperior': '²', 'onesuperior': '¹'}

# שמות גליפים עבריים — חלק מהפונטים משתמשים בשם חשוף ('het') וחלק
# בסיומת ('hethebrew'); שניהם מטופלים ב-glyphname_char
HEBREW_GLYPH_NAMES = {
    'alef': 'א', 'bet': 'ב', 'gimel': 'ג', 'dalet': 'ד', 'he': 'ה',
    'vav': 'ו', 'zayin': 'ז', 'het': 'ח', 'tet': 'ט', 'yod': 'י',
    'kaf': 'כ', 'kaffinal': 'ך', 'finalkaf': 'ך', 'lamed': 'ל',
    'mem': 'מ', 'memfinal': 'ם', 'finalmem': 'ם', 'nun': 'נ',
    'nunfinal': 'ן', 'finalnun': 'ן', 'samekh': 'ס', 'ayin': 'ע',
    'pe': 'פ', 'pefinal': 'ף', 'finalpe': 'ף', 'tsadi': 'צ',
    'tsadifinal': 'ץ', 'finaltsadi': 'ץ', 'qof': 'ק', 'resh': 'ר',
    'shin': 'ש', 'tav': 'ת',
}


def tounicode_map(doc, xref):
    """מיפוי קוד → תו מתוך ה-CMap שב-/ToUnicode של הפונט.

    פונטי TrueType בדפים (Vilna, Rashi_rc_Fix_Shas וכד') אינם נושאים שמות
    גליפים, ולכן MuPDF פולט עבורם את הקוד הגולמי (תווי בקרה). ה-CMap הוא
    המיפוי הרשמי של ה-PDF, והוא מחזיר את תווי הביניים שהמפענחים כאן
    כבר יודעים לתרגם לעברית.
    """
    try:
        obj = doc.xref_object(xref)
        m = re.search(r'/ToUnicode\s+(\d+)\s+0\s+R', obj)
        if not m:
            return {}
        text = doc.xref_stream(int(m.group(1))).decode('latin-1', 'replace')
    except Exception:
        return {}
    out = {}
    for lo, hi, dst in re.findall(
            r'<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>', text):
        base = int(dst, 16)
        for i in range(int(lo, 16), int(hi, 16) + 1):
            out[chr(i)] = chr(base + i - int(lo, 16))
    for src, dst in re.findall(r'<([0-9a-fA-F]{2,4})>\s*<([0-9a-fA-F]{4,})>(?!\s*<)',
                               text):
        out[chr(int(src, 16))] = chr(int(dst[:4], 16))
    return out


def glyphname_char(gname):
    """התו שאותו גליף מייצג, לפי שמו."""
    if gname in HEBREW_GLYPH_NAMES:
        return HEBREW_GLYPH_NAMES[gname]
    if gname.endswith('hebrew') and gname[:-6] in HEBREW_GLYPH_NAMES:
        return HEBREW_GLYPH_NAMES[gname[:-6]]
    if gname in EXTRA_GLYPH_NAMES:
        return EXTRA_GLYPH_NAMES[gname]
    if gname in NON_AGL:
        return NON_AGL[gname]
    if gname in agl.AGL2UV:
        return chr(agl.AGL2UV[gname])
    if gname in agl.LEGACY_AGL2UV:
        return chr(agl.LEGACY_AGL2UV[gname][0])
    return None


def differences_map(doc, xref):
    """מיפוי קוד → תו מתוך /Encoding /Differences שבמילון הפונט ב-PDF.

    זהו המקור המוסמך לגליפים ששמם אינו סטנדרטי (למשל `applelogo`, שהוא
    בפועל האות נ). ה-CMap שב-/ToUnicode פשוט מדלג עליהם, ולכן MuPDF
    פולט עבורם את הקוד הגולמי — ומכאן תווי הבקרה בטקסט.
    """
    try:
        obj = doc.xref_object(xref)
        m = re.search(r'/Encoding\s+(\d+)\s+0\s+R', obj)
        if not m:
            return {}
        enc = doc.xref_object(int(m.group(1)))
        diff = re.search(r'/Differences\s*\[(.*?)\]', enc, re.S)
        if not diff:
            return {}
    except Exception:
        return {}
    names, code = {}, 0
    for tok in re.findall(r'\d+|/[^\s/\]]+', diff.group(1)):
        if tok[0] == '/':
            names[chr(code)] = tok[1:]
            code += 1
        else:
            code = int(tok)
    # פונט שכל תוכנו גליף אחד בשם threesuperior הוא הקישוט המפריד.
    # המיפוי כולל גם את התו ש-MuPDF פולט בפועל עבור אותו שם גליף.
    if names and set(names.values()) == {'threesuperior'}:
        out = {k: ORNAMENT for k in names}
        out[EXTRA_GLYPH_NAMES['threesuperior']] = ORNAMENT
        return out
    out = {}
    for k, gname in names.items():
        ch = glyphname_char(gname)
        if ch:
            out[k] = ch
    return out


_DIFF_CACHE = {'doc': None, 'maps': {}}


def glyphname_char_for_code(doc, xref, code):
    """התו של קוד מסוים לפי /Differences של הפונט, עם מטמון פר-מסמך.

    המטמון מתאפס במעבר בין מסמכים: מספרי xref חוזרים על עצמם בין קבצים,
    ומטמון לפי xref בלבד מזליג מיפויים מדף אחד לדף אחר באותו תהליך
    (למשל בריצת אצווה על כל הש"ס)."""
    if _DIFF_CACHE['doc'] is not doc:
        _DIFF_CACHE['doc'] = doc
        _DIFF_CACHE['maps'] = {}
    maps = _DIFF_CACHE['maps']
    if xref not in maps:
        maps[xref] = differences_map(doc, xref)
    return maps[xref].get(chr(code))


def build_fixmaps(doc, page):
    """לכל פונט בעמוד: מיפוי קוד-גולמי → התו הנכון."""
    fixmaps = {}
    if not HAVE_FONTTOOLS:
        return fixmaps
    import io as _io
    for xref, ext, subtype, name, ref, enc in page.get_fonts():
        short = name.split('+')[-1]
        if ext != 'cff':
            # פונט שאינו CFF — המיפוי מגיע מה-CMap של ה-PDF, ורק עבור
            # קודים שנותרו כתווי בקרה (השאר כבר תורגמו ע"י MuPDF)
            df = differences_map(doc, xref)
            tu = dict(tounicode_map(doc, xref))
            tu.update(df)                           # ה-Differences גובר
            if set(df.values()) != {ORNAMENT}:
                # רק קודים שנותרו כתווי בקרה; פונט קישוט ממופה כולו
                tu = {k: v for k, v in tu.items()
                      if ord(k) < 0x20 or ord(k) == 0x7F}
            if tu:
                fixmaps.setdefault(short, {}).update(tu)
            continue
        try:
            # /Differences של ה-PDF הוא מקור מוסמך לכל פונט, כולל CFF
            # שה-Encoding הפנימי שלו אינו שמיש (ExpertEncoding וכד')
            fm = {}
            for k, v in differences_map(doc, xref).items():
                if ord(k) < 0x20 or ord(k) == 0x7F or v == ORNAMENT:
                    fm[k] = v
            _, _, _, buf = doc.extract_font(xref)
            cff = CFFFontSet()
            cff.decompile(_io.BytesIO(buf), None)
            font = cff[cff.fontNames[0]]
            encoding = font.Encoding
            if not isinstance(encoding, list):
                if fm:
                    fixmaps[short] = fm
                continue
            names = [g for g in encoding if g not in ('.notdef', None)]
            for code, gname in enumerate(encoding):
                if gname in ('.notdef', None):
                    continue
                # כל המפתחות שייתכן ש-MuPDF יפלוט עבור הקוד הזה
                keys = {chr(code)}
                if gname in agl.AGL2UV:
                    keys.add(chr(agl.AGL2UV[gname]))
                if gname in EXTRA_GLYPH_NAMES:
                    keys.add(EXTRA_GLYPH_NAMES[gname])
                if names == ['threesuperior']:
                    # פונט שכל-כולו גליף קישוט מפריד
                    for k in keys:
                        fm[k] = ORNAMENT
                elif gname not in agl.AGL2UV and gname in NON_AGL:
                    for k in keys:
                        fm[k] = NON_AGL[gname]
            if fm:
                fixmaps[short] = fm
        except Exception:
            continue
    return fixmaps


def ttf_family(name):
    """שם משפחה תקני לפונט TrueType, ישירות משמו ב-PDF."""
    base = re.sub(r'[^A-Za-z0-9]', '', name.split('+')[-1])
    return 'Shas' + base[:1].upper() + base[1:]


def build_font_table(chars, ttf_names=()):
    """לכל פונט: קידוד, סוג כתב ומשפחת הגופן.

    לפונטי TrueType ה-PDF מצהיר על שם הגופן, ולכן המשפחה נלקחת ממנו
    ישירות — ללא ניחוש. רק לתתי-פונט CFF, שנקראים TT44D2Fo00 וכד',
    נדרש סיווג לפי הקידוד והגודל."""
    from collections import Counter
    samples, sizes = {}, {}
    for c in chars:
        if len(samples.setdefault(c['font'], [])) < 400:
            samples[c['font']].append(c['c'])
        sizes.setdefault(c['font'], Counter())[round(c['size'], 1)] += 1
    table = {}
    for font, cs in samples.items():
        enc = detect_encoding(''.join(cs))
        size = sizes[font].most_common(1)[0][0]
        # הדפוס משתמש בחיתוך אופטי שונה לגדלים קטנים — ולכן פונט נפרד
        small = size < 9.0
        orn_chars = set(''.join(cs)) - {' '}
        if orn_chars and orn_chars <= {ORNAMENT, '³'} and size >= 15:
            # פונט קישוט: לעיתים הגליף ממופה כ-threesuperior ('³') בלי
            # שהעטיפה זיהתה אותו; הזיהוי כאן — לפי תוכן הפונט וגודלו
            fam, enc = 'or', 'ornament'
        elif enc == 'latin1':
            fam = 'dh' if size >= 14 else ('rss' if small else 'rs')
        elif enc == 'unicode':
            fam = 'bd'
        elif enc == 'si960':
            fam = 'to'
        else:
            fam = 'sqs' if small else 'sq'
        script = 'rashi' if enc == 'latin1' else 'square'
        if font.split('+')[-1] in ttf_names and fam != 'or':
            fam = ttf_family(font)
            script = 'rashi' if 'rashi' in fam.lower() else 'square'
        table[font] = {'enc': enc, 'fam': fam, 'script': script}
    return table


# ---------------------------------------------------------------- line building

MIRROR = str.maketrans('()[]{}<>', ')(][}{><')


def group_lines(chars, ftab):
    """קיבוץ תווים לשורות פיזיות לפי baseline, ופיצול לעמודות לפי מרזבים מקומיים."""
    def visible(c):
        if not c['c'].strip():
            return False
        # גליף ברוחב אפס שמפוענח לתו בקרה = תו-עזר של מחולל ה-PDF,
        # ללא דיו במקור — מושמט (סימני ניקוד ברוחב אפס מפוענחים לניקוד
        # אמיתי ולכן נשארים)
        if c['bbox'][2] - c['bbox'][0] < 0.01:
            d = DECODERS[ftab[c['font']]['enc']](c['c'])
            if not d or ord(d[0]) < 0x20:
                return False
        return True

    solid = [c for c in chars if visible(c)]
    spaces = [c for c in chars if not c['c'].strip()]

    # קיבוץ לפי baseline — סובלנות יחסית לגודל הפונט
    solid = sorted(solid, key=lambda c: (c['oy'], c['bbox'][0]))
    rows = []
    for c in solid:
        # התאמה לשורה הקרובה ביותר בלבד. הסף נגזר מהגופן הקטן מבין השניים,
        # אחרת תו מעמודה צפופה נבלע לשורה של עמודה בגופן גדול שלידה,
        # ושארית השורה נראית "מוזחת פנימה".
        best, best_d = None, None
        for r in rows[-10:]:
            d = abs(c['oy'] - r['oy'])
            ratio0 = min(c['size'], r['size']) / max(c['size'], r['size'])
            # כשהגדלים רחוקים זה מזה מדובר כמעט תמיד באזורים שונים בדף,
            # ולכן הסף מוקטן (למשל כותרת קטנה ליד מספר הדף הגדול)
            tol = 0.34 * min(c['size'], r['size']) * (1.0 if ratio0 > 0.6 else 0.55)
            # עוגן הערה מוגבה: הקטן מבין השניים יושב מעט מעל שורת הבסיס
            # של הגדול. הבדיקה סימטרית — העוגן עשוי להיסרק לפני השורה.
            if c['size'] < r['size']:
                small_oy, big_oy, big_sz = c['oy'], r['oy'], r['size']
                ratio = c['size'] / r['size']
            else:
                small_oy, big_oy, big_sz = r['oy'], c['oy'], c['size']
                ratio = r['size'] / c['size']
            if d < tol and (best_d is None or d < best_d):
                best, best_d = r, d
        if best is not None:
            best['chars'].append(c)
        else:
            rows.append({'oy': c['oy'], 'size': c['size'], 'chars': [c]})

    # מעבר נוסף: צירוף עוגני הערות (תווים קטנים ומוגבהים) לשורת הגוף
    # שלהם. הצירוף נעשה כאן ולא בלולאה שלמעלה, כי העוגן נסרק לפני השורה
    # (ה-baseline שלו גבוה יותר) והיה "תופס" את השורה לעצמו — ואז הטקסט
    # הראשי נבנה כשורה נפרדת, שנדפסת מעל העוגן.
    rows.sort(key=lambda r: r['oy'])
    for r in rows:
        if not r['chars'] or len(r['chars']) > 6:
            continue
        sz = max(c['size'] for c in r['chars'])
        rx0 = min(c['bbox'][0] for c in r['chars'])
        rx1 = max(c['bbox'][2] for c in r['chars'])
        for o in rows:
            if o is r or not o['chars']:
                continue
            osz = max(c['size'] for c in o['chars'])
            if sz > 0.85 * osz or not 0 <= o['oy'] - r['oy'] < 0.35 * osz:
                continue
            if any(c['bbox'][0] - 1.5 * sz <= rx1 and rx0 <= c['bbox'][2] + 1.5 * sz
                   for c in o['chars']):
                o['chars'].extend(r['chars'])
                r['chars'] = []
                break
    rows = [r for r in rows if r['chars']]

    # --- מסדרוני עמודות: רצועות אנכיות ריקות שנמשכות לאורך הדף.
    # רק בהן מותר לפצל שורה. חישוב גלובלי (ולא בדיקה מקומית סביב הפער)
    # מונע פיצול-שווא של שורה רצופה שיש בה ציון בגופן קטן או הערת שוליים.
    XB, YB = 1.0, 2.0           # רזולוציית הרשת (נקודות)
    MIN_CORRIDOR = 30.0         # אורך אנכי מזערי של מסדרון אמיתי
    MIN_SIDE = 2.0             # ...ולפחות כך לכל כיוון
    MIN_SUPPORT = 3             # כמה שורות צריכות להתפצל באותו x
    occupied = {}
    for c in solid:
        x0, y0, x1, y1 = c['bbox']
        yb0, yb1 = int(y0 // YB), int(y1 // YB)
        for xb in range(int(x0 // XB), int(x1 // XB) + 1):
            s = occupied.setdefault(xb, set())
            for yb in range(yb0, yb1 + 1):
                s.add(yb)

    def corridor_span(x, oy):
        """אורך הרצועה האנכית הריקה מעל ומתחת ל-oy במיקום האופקי x."""
        xb = int(x // XB)
        occ = occupied.get(xb, set()) | occupied.get(xb - 1, set()) \
            | occupied.get(xb + 1, set())
        yb = int(oy // YB)
        up = dn = 0
        while yb - up - 1 not in occ and up < 200:
            up += 1
        while yb + dn + 1 not in occ and dn < 200:
            dn += 1
        return up * YB, dn * YB

    def is_gutter(lo, hi, oy):
        """מועמד למסדרון עמודות: רצועה ריקה ארוכה לפחות לכיוון אחד.
        די בכיוון אחד משום שבשורה הראשונה או האחרונה של בלוק המסדרון
        נחסם מיד מהצד השני. ההכרעה הסופית נעשית לפי עקביות בין שורות."""
        x = lo
        while x <= hi:
            up, dn = corridor_span(x, oy)
            if max(up, dn) >= MIN_CORRIDOR and min(up, dn) >= MIN_SIDE:
                return True
            x += XB
        return False

    # מעבר ראשון: מועמדים לפיצול, ואיסוף קווי החיתוך שבהם הם יושבים
    cand_splits, support = [], {}
    for row in rows:
        cs = sorted(row['chars'], key=lambda c: c['bbox'][0])
        marks = []
        for a, c in zip(cs, cs[1:]):
            gap = c['bbox'][0] - a['bbox'][2]
            if gap <= 2.5:
                continue
            huge = gap > 2.2 * max(c['size'], a['size'])
            if huge or is_gutter(a['bbox'][2], c['bbox'][0], row['oy']):
                mid = (a['bbox'][2] + c['bbox'][0]) / 2
                marks.append((c, mid, huge))
                support[round(mid / 4)] = support.get(round(mid / 4), 0) + 1
        cand_splits.append((row, cs, marks))

    # מעבר שני: פיצול רק בקווי חיתוך שחוזרים על עצמם בכמה שורות — גבול
    # עמודות אמיתי עקבי לאורך הדף, בעוד פיצול-שווא (ציון בגופן קטן בתוך
    # שורה, עוגן הערה) מופיע בשורה בודדת בלבד.
    lines = []
    for row, cs, marks in cand_splits:
        at = {id(c) for c, mid, huge in marks
              if huge or max(support.get(round(mid / 4) + d, 0)
                             for d in (-1, 0, 1)) >= MIN_SUPPORT}
        chunks, cur = [], [cs[0]]
        for c in cs[1:]:
            if id(c) in at:
                chunks.append(cur)
                cur = [c]
            else:
                cur.append(c)
        chunks.append(cur)
        for chunk in chunks:
            chunk_oys = sorted(c['oy'] for c in chunk)
            oy = chunk_oys[len(chunk_oys) // 2]
            lines.append(make_line(chunk, oy, spaces, ftab))
    return lines


def make_line(chunk, oy, spaces, ftab):
    """בונה שורה לוגית מרשימת תווים: מיון ימין→שמאל, פענוח, שחזור רווחים."""
    x0 = min(c['bbox'][0] for c in chunk)
    x1 = max(c['bbox'][2] for c in chunk)
    size = max(c['size'] for c in chunk)

    # תווי הרווח האמיתיים של השורה (מה-PDF)
    row_spaces = [s for s in spaces
                  if abs(s['oy'] - oy) < 0.5 * size and x0 - 2 < s['bbox'][0] < x1 + 2]

    def is_mark(c):
        d = DECODERS[ftab[c['font']]['enc']](c['c'])
        return bool(HEB_MARK.match(d)) or (c['bbox'][2] - c['bbox'][0] < 0.01)

    # סדר קריאה: ימין לשמאל; סימן ניקוד משויך גיאומטרית לאות הקרובה
    # ביותר אליו (לפי מרכז אופקי) ונכנס מיד אחריה
    bases = sorted((c for c in chunk if not is_mark(c)),
                   key=lambda c: (-round(c['bbox'][2], 1), -c['bbox'][0]))
    marks = [c for c in chunk if is_mark(c)]
    attached = {id(b): [] for b in bases}
    if bases:
        for m in marks:
            mx = (m['bbox'][0] + m['bbox'][2]) / 2
            dm = DECODERS[ftab[m['font']]['enc']](m['c'])
            # אות שמכילה את מרכז הסימן; חולם מצויר משמאל-מעל לאות שלו,
            # ולכן בהיעדר הכלה הוא שייך לאות שמימינו
            containing = [b for b in bases if b['bbox'][0] - 0.3 <= mx <= b['bbox'][2] + 0.3]
            if 'ֹ' in dm:
                # חולם — תמיד לאות שמימין למרכזו
                right = [b for b in bases if (b['bbox'][0] + b['bbox'][2]) / 2 > mx]
                b = min(right, key=lambda b: (b['bbox'][0] + b['bbox'][2]) / 2 - mx) \
                    if right else bases[0]
            elif containing:
                b = min(containing,
                        key=lambda b: abs((b['bbox'][0] + b['bbox'][2]) / 2 - mx))
            else:
                b = min(bases,
                        key=lambda b: abs((b['bbox'][0] + b['bbox'][2]) / 2 - mx))
            attached[id(b)].append(m)
    cs = []
    for b in bases:
        cs.append(b)
        cs.extend(sorted(attached[id(b)], key=lambda m: -m['bbox'][2]))
    if not bases:
        cs = marks
    parts, cur, prev = [], None, None
    for c in cs:
        info = ftab[c['font']]
        d = DECODERS[info['enc']](c['c']).translate(MIRROR)
        sp = ''
        if prev is not None and not is_mark(c):
            lo, hi = c['bbox'][2], prev['bbox'][0]      # המרווח בקריאה RTL
            if hi - lo > 0.04 * size:
                if any(lo - 1.5 <= s['bbox'][0] <= hi + 1.5 for s in row_spaces):
                    sp = ' '
                # בגופן הזה אותיות בתוך מילה נוגעות זו בזו (פער ‎~0.00em‎),
                # ורווחי מילים מתחילים ב-‎0.13em‎ — גם בטורי השוליים הצפופים
                elif hi - lo > 0.09 * min(c['size'], prev['size']):
                    sp = ' '
        sig = (info['fam'], info['script'], round(c['size'], 1))
        if cur is None or cur['sig'] != sig or sp:
            # ריצה חדשה בכל שינוי גופן **וגם** בכל רווח: כל ריצה היא
            # יחידה שתמוקם בנפרד לפי המיקום המדויק שלה ב-PDF
            if cur:
                if not sp and prev is not None and not is_mark(c) and \
                        prev['bbox'][0] - c['bbox'][2] > 0.1 * min(c['size'], prev['size']):
                    sp = ' '
                cur['sp'] = bool(sp)
                parts.append(cur)
            cur = {'sig': sig, 'text': '', 'script': info['script'],
                   'fam': info['fam'], 'size': c['size'], 'sp': False,
                   'x0': c['bbox'][0], 'x1': c['bbox'][2], 'oy': c['oy']}
        cur['text'] += d
        cur['x0'] = min(cur['x0'], c['bbox'][0])
        cur['x1'] = max(cur['x1'], c['bbox'][2])
        if not is_mark(c):
            prev = c
    if cur:
        parts.append(cur)

    return {
        'x0': x0, 'x1': x1,
        'y0': oy - 0.86 * size, 'y1': oy + 0.22 * size, 'oy': oy,
        'size': size,
        'parts': [{'text': p['text'], 'script': p['script'],
                   'fam': p['fam'], 'size': p['size'], 'sp': p['sp'],
                   'x0': p['x0'], 'x1': p['x1'], 'oy': p['oy']}
                  for p in parts],
    }


# ---------------------------------------------------------------- zones

def gemara_metrics(lines):
    """מאתר את גוש הגמרא ואת גודל גופו — הכל נגזר מהדף עצמו.

    הגמרא היא הכתב המרובע הגדול ביותר שיש לו נפח טקסט ממשי: השוליים
    מרובעים אף הם אך קטנים בהרבה, והכותרות גדולות אך זעירות בנפחן.
    סף גודל קבוע (12.5) נשבר במסכתות שגופן הגמרא בהן קטן יותר — במנחות
    למשל הוא 11.5, ושם הזיהוי הישן החזיר גוש שגוי לגמרי.
    """
    from collections import Counter
    cands = [l for l in lines if l['y0'] > 28 and
             max(l['parts'], key=lambda p: len(p['text']))['script'] == 'square']
    mass = Counter()
    for l in cands:
        mass[round(l['size'], 1)] += sum(len(p['text']) for p in l['parts'])
    total = sum(mass.values())
    big = [sz for sz, m in mass.items() if m >= 0.10 * total]
    if not big:
        return (200, 450, 60, 700), 13.7
    gsize = max(big)
    sel = [l for l in cands if abs(l['size'] - gsize) < 0.6]
    return (min(l['x0'] for l in sel), max(l['x1'] for l in sel),
            min(l['y0'] for l in sel), max(l['y1'] for l in sel)), gsize


def gemara_bbox(lines):
    return gemara_metrics(lines)[0]


def body_size(lines, gemara_box=None):
    """גודל גוף הגמרא — קנה המידה להבחנה בין טורי הפירוש לטורי השוליים."""
    return gemara_metrics(lines)[1]


def classify_lines(lines, gemara_box, rashi_side='right'):
    """מסווג את כל השורות, ואז מצרף לטורי השוליים גם את מה שיושב בתוכם
    גיאומטרית — כותרות המדורים ("מסורת הש"ס", "תורה אור השלם") מודפסות
    בגופן גדול מגוף המדור, ולכן מבחן הגודל לבדו מפספס אותן."""
    gsz = gemara_metrics(lines)[1]
    zones = {id(l): classify(l, gemara_box, rashi_side, gsz) for l in lines}
    for side in ('margin-left', 'margin-right'):
        cols = [l for l in lines if zones[id(l)] == side]
        if not cols:
            continue
        lo = min(l['x0'] for l in cols) - 2
        hi = max(l['x1'] for l in cols) + 2
        for l in lines:
            if zones[id(l)] in ('rashi', 'tosafot') and lo <= l['x0'] and l['x1'] <= hi:
                zones[id(l)] = side
    return zones


def classify(line, gemara_box, rashi_side='right', gsize=None):
    x0, x1, y0 = line['x0'], line['x1'], line['y0']
    cx = (x0 + x1) / 2
    size = line['size']
    main_script = max(line['parts'], key=lambda p: len(p['text']))['script']

    if y0 < 28:
        return 'header'
    gx0, gx1, gy0, gy1 = gemara_box
    big = size >= 0.9 * gsize if gsize else size >= 12.5
    if big and main_script == 'square' and gx0 - 10 <= cx <= gx1 + 10:
        return 'gemara'
    if y0 > gy1 + 8:
        return 'bottom'
    # טורי השוליים מודפסים בגופן קטן בהרבה מהפירושים (‎~0.5‎ מול ‎~0.8‎
    # מגוף הגמרא). ההבחנה לפי יחס-גודל תקפה בכל מסכת, בעוד סף x קבוע
    # נשבר בדפים שגיאומטריית העמודות שלהם שונה.
    if gsize and size < 0.65 * gsize and not (gx0 - 10 <= cx <= gx1 + 10):
        return 'margin-right' if cx > (gx0 + gx1) / 2 else 'margin-left'
    right = cx > (gx0 + gx1) / 2
    if rashi_side == 'right':
        return 'rashi' if right else 'tosafot'
    return 'tosafot' if right else 'rashi'


# ---------------------------------------------------------------- html

CSS_HEAD = """
:root { --page-w:%(w)spx; --page-h:%(h)spx; }
"""
FACE = ("@font-face { font-family:'%(name)s'; "
        "src:url('%(dir)s/%(name)s.woff2') format('woff2'); }")

# הפונטים המקוריים חולצו מה-PDF (ראו extract_fonts.py) — לכן אין צורך
# בכיול גבהים: כל חלק מוצג בפונט-המקור שלו ובגודל הנומינלי המקורי.
FAM_CLASS = {'sq': 'f-sq', 'sqs': 'f-sqs', 'rs': 'f-rs', 'rss': 'f-rss',
             'dh': 'f-dh', 'bd': 'f-bd', 'to': 'f-to', 'or': 'f-or'}
# שם קובץ הגופן לכל משפחה (למשפחות ה-TrueType השם הוא המשפחה עצמה)
FAM_FILE = {'sq': 'ShasSquare', 'sqs': 'ShasSquareSm', 'rs': 'ShasRashi',
            'rss': 'ShasRashiSm', 'dh': 'ShasDHBig', 'bd': 'ShasBold',
            'to': 'ShasTorahOr', 'or': 'ShasOrnament'}


def _zone_body_size(zlines):
    """גודל גוף הטקסט השכיח (במשקל תווים) של כתב רש"י באזור."""
    from collections import Counter
    cnt = Counter()
    for ln in zlines:
        for p in ln['parts']:
            if p['script'] == 'rashi':
                cnt[round(p['size'], 1)] += len(p['text'])
    return cnt.most_common(1)[0][0] if cnt else 11.2


def _dh_state(part, line_size, body_size):
    """True=ד"ה, False=גוף, None=ניטרלי (פיסוק — ממשיך את המצב הנוכחי).
    ד"ה מזוהה בשתי צורות: ריצת מרובע בגודל שורה מלא (כמו ברש"י כאן),
    או כתב רש"י גדול מגוף האזור (המילה הראשונה וההמשך בתוס')."""
    heb = HEB.findall(part['text'])
    if not heb:
        return None
    if part['script'] == 'square' and part['size'] >= 0.95 * line_size and len(heb) >= 2:
        return True
    if part['script'] == 'rashi' and part['size'] >= body_size + 0.3:
        return True
    return False


def assign_segments(lines, gb, rashi_side):
    """מחלק את רש"י והתוס' למקטעים שלמים (דיבור־המתחיל עד הבא אחריו).
    כל חלק-שורה מקבל part['seg'] ('r3'/'t1') ו-part['dh'];
    מקטע 0 = המשך מהעמוד הקודם."""
    zmap = classify_lines(lines, gb, rashi_side)
    for zone, prefix in (('rashi', 'r'), ('tosafot', 't')):
        zlines = [ln for ln in lines if zmap[id(ln)] == zone]
        zlines.sort(key=lambda l: (l['y0'], -l['x1']))
        body = _zone_body_size(zlines)
        seg, in_dh = 0, False
        for ln in zlines:
            for p in ln['parts']:
                dh = _dh_state(p, ln['size'], body)
                if dh is None:
                    dh = in_dh        # פיסוק נגרר אחרי שכניו
                elif dh and not in_dh:
                    seg += 1          # ד"ה חדש פותח מקטע
                in_dh = dh
                p['seg'] = f'{prefix}{seg}'
                p['dh'] = dh


def part_class_size(zone, part, line_size):
    """מחזיר (class, display_size): משפחת הפונט המקורי של החלק כפי שחולץ
    מה-PDF, בגודל הנומינלי המקורי — התאמה מלאה בגובה, ברוחב ובמשקל."""
    fam = part.get('fam') or ('rs' if part['script'] == 'rashi' else 'sq')
    cls = FAM_CLASS.get(fam, 'f-sq')
    if part.get('dh'):
        cls += ' dh'
    return cls, part['size']



def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def render_html(lines, page_w, page_h, fonts_rel, title, rashi_side='right',
                assets_rel='.'):
    out = []
    out.append('<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8">')
    out.append(f'<title>{esc(title)}</title>')
    # @font-face רק לגופנים שהדף באמת משתמש בהם — כולל פונטי ה-TrueType
    # שלו, שנקצרו לקבצים נפרדים על שם הגופן שב-PDF
    used = sorted({FAM_FILE.get(p.get('fam', 'sq'), p.get('fam', 'sq'))
                   for ln in lines for p in ln['parts']})
    faces = '\n'.join(FACE % {'name': n, 'dir': fonts_rel} for n in used if n)
    out.append('<style>%s\n%s</style>' % (
        faces, CSS_HEAD % {'w': round(page_w, 2), 'h': round(page_h, 2)}))
    out.append(f'<link rel="stylesheet" href="{assets_rel}/daf.css">')
    ttf_css = '\n'.join(f"span.f-{n} {{ font-family:'{n}',serif; }}"
                        for n in used if n.startswith('Shas') and n not in FAM_FILE.values())
    if ttf_css:
        out.append('<style>%s</style>' % ttf_css)
    out.append('</head><body class="daf-standalone">')
    out.append(f'<div class="daf-page" data-rashi-side="{rashi_side}">')
    # כל ריצת-טקסט ממוקמת בנפרד לפי המיקום המדויק שלה ב-PDF. כך צורת
    # הדף אינה תלויה כלל בקיבוץ לשורות או בזיהוי גבולות עמודות: גם אם
    # הקיבוץ שוגה, כל מילה עדיין נוחתת במקומה המדויק ושום דבר לא נדרס
    # ולא נמתח. הקיבוץ נשאר רק לצורכי סמנטיקה (אזור, מקטע, חיפוש).
    for ln in sorted(lines, key=lambda l: (l['y0'], -l['x1'])):
        style = (f"right:{page_w - ln['x1']:.1f}px;top:{ln['y0']:.1f}px;"
                 f"width:{ln['x1'] - ln['x0']:.1f}px")
        spans = []
        for p in ln['parts']:
            fam = p.get('fam', 'sq')
            cls = FAM_CLASS.get(fam) or 'f-' + fam
            # line-height אחיד (1.08) מוגדר ב-CSS, ו-top נכתב רק כשהוא
            # חורג משורת הבסיס — כך רוב הריצות מסתפקות ב-right ובגודל
            top = p['oy'] - 0.86 * p['size'] - ln['y0']
            wstyle = f"right:{ln['x1'] - p['x1']:.1f}px"
            if abs(top) >= 0.05:
                wstyle += f";top:{top:.1f}px"
            wstyle += f";font-size:{p['size']:.1f}px"
            spans.append(f'<span class="w {cls}" style="{wstyle}"'
                         f' data-w="{p["x1"] - p["x0"]:.1f}"'
                         f'>{esc(p["text"])}</span>')
            if p.get('sp'):
                spans.append(' ')
        # הרווח בסוף השורה הופך את ההעתקה לקטע טקסט רציף — בלי שבירת
        # שורות ובלי שמילת סוף-שורה תידבק למילה הראשונה של הבאה
        out.append(f'<div class="ln" style="{style}"'
                   f' data-x0="{ln["x0"]:.1f}" data-x1="{ln["x1"]:.1f}"'
                   f' data-size="{ln["size"]:.1f}"'
                   f'>{"".join(spans)} </div>')
    out.append('</div>')
    out.append(f'<script src="{assets_rel}/daf.js"></script>')
    out.append('</body></html>')
    return '\n'.join(out)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('masechta', nargs='?', help='masechta folder index (0-39)')
    ap.add_argument('page', nargs='?', help='page file index (e.g. 2)')
    ap.add_argument('--pdf', help='direct path to a decoded PDF')
    ap.add_argument('--out', default='daf.html')
    ap.add_argument('--fonts', default='fonts', help='relative URL to fonts dir')
    ap.add_argument('--assets', default='.',
                    help='relative URL to the dir holding daf.css / daf.js')
    ap.add_argument('--dump-json', help='also dump structured lines JSON')
    ap.add_argument('--dump-text', help='dump per-zone text JSON (for search indexing)')
    args = ap.parse_args()

    if args.pdf:
        pdf_bytes = Path(args.pdf).read_bytes()
        title = Path(args.pdf).stem
    else:
        js = SHAS_DIR / args.masechta / f'{args.page}.js'
        pdf_bytes = load_pdf(js)
        title = f'{args.masechta}/{args.page}'

    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    page = doc[0]
    fixmaps = build_fixmaps(doc, page)
    chars = extract_chars(page, fixmaps)
    ttf_names = {f[3].split('+')[-1] for f in page.get_fonts() if f[1] == 'ttf'}
    ftab = build_font_table(chars, ttf_names)
    lines = group_lines(chars, ttf_names and ftab or ftab)
    try:
        rashi_side = 'right' if int(args.page or 0) % 2 == 0 else 'left'
    except (TypeError, ValueError):
        rashi_side = 'right'
    html = render_html(lines, page.rect.width, page.rect.height, args.fonts,
                       title, rashi_side, args.assets)
    Path(args.out).write_text(html)
    print(f'{len(chars)} chars, {len(lines)} lines -> {args.out}')

    if args.dump_json:
        Path(args.dump_json).write_text(
            json.dumps(lines, ensure_ascii=False, indent=1))

    if args.dump_text:
        # טקסט רציף לכל שכבה + מקטעי רש"י/תוס' שלמים — בסיס לאינדוקס חיפוש
        gb = gemara_bbox(lines)
        zmap = classify_lines(lines, gb, rashi_side)
        zones, segs = {}, {}
        for ln in sorted(lines, key=lambda l: (l['y0'], -l['x1'])):
            z = zmap[id(ln)]
            t = ''.join(p['text'] + (' ' if p.get('sp') else '')
                        for p in ln['parts']).strip()
            if t and set(t) != {ORNAMENT}:
                zones.setdefault(z, []).append(t)
            for p in ln['parts']:
                if p.get('seg'):
                    e = segs.setdefault(p['seg'], {'dh': '', 'text': ''})
                    e['dh' if p.get('dh') else 'text'] += \
                        p['text'] + (' ' if p.get('sp') else '')
        def _k(s):
            return (s[0], int(s[1:]))
        Path(args.dump_text).write_text(json.dumps({
            'zones': {z: ' '.join(ts) for z, ts in zones.items()},
            'segments': {s: {'dh': v['dh'].strip(), 'text': v['text'].strip()}
                         for s, v in sorted(segs.items(), key=lambda x: _k(x[0]))},
        }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
