#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_fonts — חילוץ הפונטים המקוריים מדפי הש"ס (PDF) והמרה ל-woff2.

כל דף מטמיע עשרות תתי-פונט (subsets) עם קידודים שבורים. הסקריפט קוצר
גליפים מדפים רבים, ממפה כל גליף לאות היוניקוד שלו (באותו צינור פענוח של
daf2html), ממזג לפי משפחה, ובונה פונט OTF/woff2 שלם לכל משפחה:

  ShasSquare  — הכתב המרובע (גמרא, שוליים)         [קידוד macroman]
  ShasRashi   — כתב רש"י (גוף רש"י/תוס')            [קידוד latin1, גודל < 14]
  ShasDHBig   — המילה הראשונה הגדולה בד"ה תוס'      [קידוד latin1, גודל ≥ 14]
  ShasBold    — הד"ה המודגשים                       [קידוד unicode]

שימוש:  python extract_fonts.py [--pages 40] [--out demo/fonts]
"""
import argparse
import io
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf
from fontTools.cffLib import CFFFontSet
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools import agl

sys.path.insert(0, str(Path(__file__).parent))
import daf2html as D

FAMILIES = {
    'sq': 'ShasSquare',      # מרובע גדול — גמרא
    'sqs': 'ShasSquareSm',   # מרובע קטן — שוליים (חיתוך אופטי רחב יותר)
    'rs': 'ShasRashi',       # כתב רש"י — גוף רש"י/תוס'
    'rss': 'ShasRashiSm',    # כתב רש"י קטן — שוליים
    'dh': 'ShasDHBig',       # המילה הגדולה בד"ה תוס'
    'bd': 'ShasBold',        # ד"ה מודגשים
    'to': 'ShasTorahOr',     # פסוקי תורה אור השלם (עם ניקוד)
    'or': 'ShasOrnament',    # הקישוט המפריד בין מדורי השוליים
}
# הדפוס משתמש בחיתוך אופטי שונה לגדלים קטנים (רחב יותר לקריאוּת)
SMALL_SIZE = 9.0
# תווים שכדאי לקצור לכל משפחה — כולל סימני-דפוס מיוחדים (עיגול ההפניה
# שמגיע מהגופן כתו '$', וכד') כדי שיוצגו בצורתם המקורית
WANTED_EXTRA = set(".:,;()[]'\"-!?0123456789״׳$¢£§¶*&/\\@#%+=<>|~^`")
HEBREW = set(chr(c) for c in range(0x5D0, 0x5EB))
NIKUD = set(chr(c) for c in range(0x591, 0x5C8))

# צורות מורכבות (אות+ניקוד) שיש להן גליף אחד בגופן — נבנות אוטומטית
# מטבלת ה-Presentation Forms של יוניקוד
PRECOMPOSED = {}
for _cp in range(0xFB1D, 0xFB4F):
    _d = unicodedata.decomposition(chr(_cp))
    if _d and not _d.startswith('<'):
        PRECOMPOSED[''.join(chr(int(x, 16)) for x in _d.split())] = chr(_cp)

# שמות גליפים תיאוריים ('reshhebrew') שבפונטי הד"ה המודגשים
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


def cs_width(ch):
    """רוחב הגליף. ב-CFF הרוחב נרשם בגליף רק כשהוא שונה מברירת המחדל
    של ה-Private dict — אחרת יש ליפול חזרה ל-defaultWidthX."""
    w = getattr(ch, 'width', None)
    if w is None:
        priv = getattr(ch, 'private', None)
        w = getattr(priv, 'defaultWidthX', 0) if priv else 0
    return w or 0


def bucket_of(enc, size):
    if enc == 'macroman':
        return 'sq' if size >= SMALL_SIZE else 'sqs'
    if enc == 'latin1':
        if size >= 14:
            return 'dh'
        return 'rs' if size >= SMALL_SIZE else 'rss'
    if enc == 'unicode':
        return 'bd'
    if enc == 'si960':
        return 'to'
    return None


def is_ornament_font(fixmap):
    """תת-פונט שכל תוכנו גליף הקישוט המפריד."""
    return bool(fixmap) and set(fixmap.values()) == {D.ORNAMENT}


def same_cut(cand, ref):
    """האם תת-הפונט הוא אותו חיתוך אופטי של הגופן?

    ה-PDF מכיל כמה חיתוכים של אותה משפחה (למשל מרובע צר לגמרא ורחב
    לשוליים): באחד ב'=386 ז'=193, בשני ב'=411 ז'=274. עירוב ביניהם
    נותן אותיות בודדות בעלות מראה זר. ההשוואה היא על רוחבי האותיות
    המשותפות — אותו חיתוך => יחס ‎~1.0‎."""
    shared = [c for c in cand if c in ref and ref[c] and cand[c]]
    if not ref:
        return True
    if len(shared) < 2:
        return False        # אין מספיק ראיות — נחכה לתת-פונט אחר
    ratios = sorted(cand[c] / ref[c] for c in shared)
    med = ratios[len(ratios) // 2]
    return 0.97 <= med <= 1.03


def space_widths(chars, ftab):
    """רוחב הרווח בפועל לכל משפחה, מתוך תווי הרווח של ה-PDF.
    בגופנים המקוריים אין גליף רווח; בלעדיו הדפדפן משתמש ברווח של גופן
    חלופי, והשורות יוצאות דחוסות ולא מיושרות.

    נלקח אחוזון נמוך — הריווח ההדוק ביותר שהדפוס משתמש בו. השורה
    בדפדפן מיושרת לשני הצדדים, ולכן עדיף שרוחבה הטבעי יהיה קטן מהקופסה
    והיישור ירחיב את הרווחים (כמו במקור), מאשר שיגלוש וייאלץ דחיסה."""
    acc = {}
    for c in chars:
        if not c['c'].strip() and c['size']:
            fam = ftab[c['font']]['fam']
            acc.setdefault(fam, []).append(
                (c['bbox'][2] - c['bbox'][0]) / c['size'] * 1000)
    out = {}
    for f, v in acc.items():
        v.sort()
        out[f] = max(110.0, v[int(len(v) * 0.03)])
    return out


def ttf_family(name):
    """שם משפחה תקני לפונט TrueType שמוטמע ב-PDF, ישירות משמו שם.
    בניגוד לתתי-פונט CFF (שנקראים TT44D2Fo00 וכד'), כאן ה-PDF מצהיר על
    שם הגופן — ולכן אין צורך בשום היוריסטיקה כדי לזהות אותו."""
    base = re.sub(r'[^A-Za-z0-9]', '', name.split('+')[-1])
    return 'Shas' + base[:1].upper() + base[1:]


def _draw_decomposed(glyf, gname, pen):
    """מצייר גליף TrueType כשהוא מפורק: components נפתחים רקורסיבית
    לקווי-מתאר עם הטרנספורמציה שלהם."""
    g = glyf[gname]
    if g.isComposite():
        for comp in g.components:
            if hasattr(comp, 'transform'):
                (a, b), (c, d) = comp.transform
            else:
                a, b, c, d = 1, 0, 0, 1
            x = getattr(comp, 'x', 0)
            y = getattr(comp, 'y', 0)
            _draw_decomposed(glyf, comp.glyphName,
                             TransformPen(pen, (a, b, c, d, x, y)))
    else:
        g.draw(pen, glyf)


def harvest_ttf_page(doc, page, ttf_store):
    """קוצר גליפים מפונטי TrueType. מסכתות שלמות בש"ס בנויות מהם, והם
    נושאים שמות אמיתיים (Vilna, Rashi_rc_Fix_Shas...) — כל אחד נבנה
    לקובץ משלו, כך שהתצוגה היא בגופן המקורי בדיוק."""
    fixmaps = D.build_fixmaps(doc, page)
    chars = D.extract_chars(page, fixmaps)
    ftab = D.build_font_table(chars)
    for xref, ext, subtype, name, ref, enc_name in page.get_fonts():
        if ext != 'ttf':
            continue
        short = name.split('+')[-1]
        info = ftab.get(short)
        if info is None:
            continue
        fam = ttf_family(name)
        try:
            _, _, _, buf = doc.extract_font(xref)
            tt = TTFont(io.BytesIO(buf), lazy=True)
            upem = tt['head'].unitsPerEm
            glyf = tt['glyf']
            try:
                gset = tt.getGlyphSet()
            except Exception:
                gset = None
            cmaps = {(t.platformID, t.platEncID): t.cmap for t in tt['cmap'].tables}
            obj = doc.xref_object(xref)
            first = int(re.search(r'/FirstChar\s+(\d+)', obj).group(1))
            wtxt = re.search(r'/Widths\s*\[([^\]]*)\]', obj)
            widths = [float(x) for x in wtxt.group(1).split()] if wtxt else []
        except Exception:
            continue
        store = ttf_store.setdefault(fam, {'upem': upem, 'glyphs': {}})
        fm = fixmaps.get(short, {})
        dec = D.DECODERS[info['enc']]
        for code in range(first, first + max(len(widths), 1)):
            gname = cmaps.get((3, 0), {}).get(0xF000 + code) \
                or cmaps.get((1, 0), {}).get(code) \
                or cmaps.get((3, 1), {}).get(code)
            if not gname or gname not in glyf:
                continue
            raw = chr(code)
            target = dec(fm.get(raw, D.glyphname_char_for_code(doc, xref, code) or raw))
            if len(target) == 2 and target in PRECOMPOSED:
                target = PRECOMPOSED[target]
            if len(target) != 1 or target in store['glyphs']:
                continue
            if target != D.ORNAMENT and target not in HEBREW \
                    and target not in WANTED_EXTRA and target not in NIKUD \
                    and not (0xFB1D <= ord(target) <= 0xFB4E):
                continue
            try:
                # פירוק גליפים מורכבים (component) לקווי-מתאר בזמן הקצירה.
                # נעשה ידנית מעל טבלת glyf, כי ב-subsets רבים טבלת hmtx
                # קטומה ו-getGlyphSet() נכשל
                rec = RecordingPen()
                _draw_decomposed(glyf, gname, rec)
                w = widths[code - first] * upem / 1000 if code - first < len(widths) else 0
                store['glyphs'][target] = (rec.value, w)
            except Exception:
                continue


def _rec_contours(rec):
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _rec_glyph(rec):
    pen = TTGlyphPen(None)
    for op, args in rec:
        getattr(pen, op)(*args)
    return pen.glyph()


def prepare_nikud_ttf(glyphs):
    """אותו טיפול שנעשה לפונט ה-CFF המנוקד, על גליפי TrueType: חילוץ
    אותיות שקיימות רק בצורה מנוקדת, והוספת סימני דגש/שי"ן כגליף ריק
    כדי שהרצף אות+ניקוד יורכב בפונט ולא ייפול לגופן חלופי."""
    decomp = {v: k for k, v in PRECOMPOSED.items()}
    by_base = {}
    for key in list(glyphs):
        base = None
        if len(key) == 2 and key[0] in HEBREW and key[1] in NIKUD:
            base = key[0]
        elif len(key) == 1 and key in decomp and decomp[key][0] in HEBREW:
            base = decomp[key][0]
        if base:
            by_base.setdefault(base, []).append(key)
    for base, keys in by_base.items():
        if base in glyphs:
            continue
        sets = [{_sig(c): c for c in _rec_contours(glyphs[k][0])} for k in keys]
        common = set(sets[0])
        for st in sets[1:]:
            common &= set(st)
        if not common and len(sets[0]) > 1:
            # צורה מנוקדת יחידה — מסירים את קו-המתאר הקטן ביותר (הניקוד)
            cs = sorted(sets[0].values(),
                        key=lambda c: len([p for _, a in c for p in a]))
            common = {_sig(c) for c in cs[1:]}
            sets[0] = {_sig(c): c for c in cs}
        if not common:
            continue
        rec = [step for sig in common for step in sets[0][sig]]
        glyphs[base] = (rec, glyphs[keys[0]][1])
    need = set()
    for seq, pre in PRECOMPOSED.items():
        if pre in glyphs:
            need.update(ch for ch in seq if ch not in glyphs)
    for ch in need:
        glyphs[ch] = ([], 0)
    for k in [k for k in glyphs if len(k) != 1]:
        del glyphs[k]


def build_ttf_font(fam, data, out_dir):
    """בונה woff2 + otf מגליפי TrueType שנקצרו."""
    glyphs = data['glyphs']
    if not glyphs:
        return None
    if any(len(c) == 1 and c in NIKUD for c in glyphs):
        prepare_nikud_ttf(glyphs)
    order = ['.notdef'] + [f'uni{ord(c):04X}' for c in sorted(glyphs)]
    fb = FontBuilder(data['upem'], isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(c): f'uni{ord(c):04X}' for c in glyphs})
    gl = {'.notdef': TTGlyphPen(None).glyph()}
    metrics = {'.notdef': (data['upem'] // 4, 0)}
    for c, (rec, w) in glyphs.items():
        n = f'uni{ord(c):04X}'
        gl[n] = _rec_glyph(rec)
        metrics[n] = (0 if c in NIKUD else max(0, int(w)), 0)
    fb.setupGlyf(gl)
    fb.setupHorizontalMetrics(metrics)
    # מטריקות אנכיות אחידות — ראו build_font
    upem = data['upem']
    asc, desc = round(0.86 * upem), -round(0.22 * upem)
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    fb.setupNameTable({'familyName': fam, 'styleName': 'Regular',
                       'fullName': fam, 'psName': fam})
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=asc, usWinDescent=-desc,
                fsSelection=0x40 | 0x80)
    fb.setupPost()
    fea = nikud_features({c: (None, w, None) for c, (_, w) in glyphs.items()})
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        try:
            addOpenTypeFeaturesFromString(fb.font, fea)
        except Exception:
            pass
    out_dir.mkdir(parents=True, exist_ok=True)
    fb.font.flavor = 'woff2'
    path = out_dir / f'{fam}.woff2'
    fb.font.save(str(path))
    otf = out_dir.parent / 'fonts-install'
    otf.mkdir(parents=True, exist_ok=True)
    fb.font.flavor = None
    fb.font.save(str(otf / f'{fam}.ttf'))
    return path


def harvest_page(doc, page, candidates):
    """אוסף מהדף מועמדים: לכל תת-פונט — הגליפים שלו ומספר התווים שבשימוש.
    המיזוג נעשה אחר כך (merge_candidates), כדי שהחיתוך הדומיננטי ינצח."""
    fixmaps = D.build_fixmaps(doc, page)
    chars = D.extract_chars(page, fixmaps)
    ftab = D.build_font_table(chars)
    for fam, w in space_widths(chars, ftab).items():
        candidates.setdefault('_space_' + fam, []).append(w)
    # גודל שימוש טיפוסי + נפח שימוש לכל פונט
    sizes = defaultdict(Counter)
    usage = Counter()
    for c in chars:
        short = c['font'].split('+')[-1]
        sizes[short][round(c['size'], 1)] += 1
        usage[short] += 1

    for xref, ext, subtype, name, ref, enc_name in page.get_fonts():
        short = name.split('+')[-1]
        if ext != 'cff' or short not in {f.split('+')[-1] for f in ftab} \
                and short not in sizes:
            continue
        info = ftab.get(short) or ftab.get(name)
        if info is None:
            # ftab ממופתח בשם המלא כפי שמופיע ב-rawdict (ללא קידומת)
            info = ftab.get(short)
        if info is None:
            continue
        size = sizes[short].most_common(1)[0][0] if sizes[short] else 0
        bucket = 'or' if is_ornament_font(fixmaps.get(short)) \
            else bucket_of(info['enc'], size)
        if bucket is None:
            continue
        try:
            _, _, _, buf = doc.extract_font(xref)
            cff = CFFFontSet()
            cff.decompile(io.BytesIO(buf), None)
            cff.desubroutinize()
            f = cff[cff.fontNames[0]]
            encoding = f.Encoding
            if not isinstance(encoding, list):
                continue
            cs = f.CharStrings
            fm = fixmaps.get(short, {})
            # נרמול לגוף 1000: חלק מתתי-הפונט משתמשים ב-FontMatrix שונה
            matrix = f.rawDict.get('FontMatrix')
            gscale = (matrix[0] * 1000) if matrix else 1.0
            harvested = {}
            for code, gname in enumerate(encoding):
                if gname in ('.notdef', None) or gname not in cs:
                    continue
                if gname.endswith('hebrew') and gname[:-6] in HEBREW_GLYPH_NAMES:
                    emitted = HEBREW_GLYPH_NAMES[gname[:-6]]
                elif gname in agl.AGL2UV:
                    emitted = chr(agl.AGL2UV[gname])
                elif gname in agl.LEGACY_AGL2UV:
                    # LEGACY_AGL2UV מחזיר רשימת קודים, לא קוד בודד
                    emitted = chr(agl.LEGACY_AGL2UV[gname][0])
                elif gname in D.EXTRA_GLYPH_NAMES:
                    emitted = D.EXTRA_GLYPH_NAMES[gname]
                else:
                    u = agl.toUnicode(gname)
                    emitted = u if len(u) == 1 else chr(code)
                emitted = fm.get(emitted, emitted)
                target = D.DECODERS[info['enc']](emitted)
                if len(target) == 2 and target in PRECOMPOSED:
                    target = PRECOMPOSED[target]      # אות+ניקוד = גליף אחד
                elif len(target) == 2 and bucket == 'to' \
                        and target[0] in HEBREW and target[1] in NIKUD:
                    pass    # צורה מורכבת ללא Presentation Form — נשמרת כרצף
                elif len(target) != 1:
                    continue
                if len(target) == 1 and target != D.ORNAMENT \
                        and target not in HEBREW and target not in WANTED_EXTRA \
                        and not (bucket == 'to' and
                                 (target in NIKUD or 0xFB1D <= ord(target) <= 0xFB4E)):
                    continue
                ch = cs[gname]
                ch.decompile()
                pen = T2CharStringPen(None, cs)
                ch.draw(pen if gscale == 1.0 else
                        TransformPen(pen, (gscale, 0, 0, gscale, 0, 0)))
                bp = BoundsPen(cs)
                ch.draw(bp if gscale == 1.0 else
                        TransformPen(bp, (gscale, 0, 0, gscale, 0, 0)))
                width = cs_width(ch) * gscale
                harvested[target] = (pen.getCharString(), width, bp.bounds)
            if harvested:
                candidates[bucket].append({'glyphs': harvested,
                                           'usage': usage[short]})
        except Exception:
            continue


def merge_candidates(cands, strict=True):
    """ממזג מועמדים לפונט אחד: מתחילים מתת-הפונט השכיח ביותר (החיתוך
    הדומיננטי), ומצרפים רק תתי-פונט שרוחביהם תואמים לו."""
    cands = sorted(cands, key=lambda c: -c['usage'])
    merged, ref, deferred = {}, {}, []
    for c in cands:
        widths = {t: w for t, (_, w, _) in c['glyphs'].items()}
        if strict and not same_cut(widths, ref):
            deferred.append(c)
            continue
        ref.update(widths)
        for t, g in c['glyphs'].items():
            merged.setdefault(t, g)
    # סבב שני: אותיות שנותרו חסרות, מתתי-פונט שנדחו רק בגלל חוסר חפיפה
    for c in deferred:
        widths = {t: w for t, (_, w, _) in c['glyphs'].items()}
        if same_cut(widths, ref):
            ref.update(widths)
            for t, g in c['glyphs'].items():
                merged.setdefault(t, g)
    # סבב שלישי: סימני פיסוק וסימני-דפוס מיוחדים. בדיקת החיתוך נועדה
    # לאותיות; סימנים נדירים (כמו עיגול ההפניה) יושבים בתתי-פונט קטנים
    # שאין להם אותיות משותפות להשוואה, ובלעדיהם הם נופלים לגופן חלופי.
    for c in cands:
        for t, g in c['glyphs'].items():
            if t not in HEBREW and t not in NIKUD:
                merged.setdefault(t, g)
    return merged


def nikud_features(glyphs):
    """קוד OpenType לפונט מנוקד: ccmp שממיר רצף אות+ניקוד לגליף המורכב
    שקיים בגופן המקורי, ו-mark שמצמיד את סימני הניקוד למרכז האות.
    בלי זה סימני הניקוד נופלים לגופן חלופי או נערמים במקום הלא נכון."""
    marks = [c for c in glyphs if c in NIKUD]
    bases = [c for c in glyphs if c in HEBREW]
    if not marks or not bases:
        return None

    def gn(c):
        return f'uni{ord(c):04X}'

    lines = []
    # ccmp: אות + ניקוד → הגליף המורכב המקורי
    subs = []
    for seq, pre in PRECOMPOSED.items():
        if pre in glyphs and all(ch in glyphs for ch in seq):
            subs.append('    sub ' + ' '.join(gn(ch) for ch in seq)
                        + f' by {gn(pre)};')
    if subs:
        lines.append('feature ccmp {\n' + '\n'.join(subs) + '\n} ccmp;')

    # mark: הצמדת ניקוד למרכז האות (הגובה כבר צרוב בגליף עצמו)
    above = [c for c in marks if c in 'ֹֺ']       # חולם — נמשך לצד שמאל-עליון
    below = [c for c in marks if c not in above]
    cls = []
    for name, group, frac in (('BELOW', below, 0.5), ('ABOVE', above, 0.2)):
        if not group:
            continue
        for c in group:
            w = glyphs[c][1] or 0
            cls.append(f'markClass {gn(c)} <anchor {int(w / 2)} 0> @MC_{name};')
    lines.extend(cls)
    pos = []
    for name, group, frac in (('BELOW', below, 0.5), ('ABOVE', above, 0.2)):
        if not group:
            continue
        for b in bases:
            w = glyphs[b][1] or 0
            pos.append(f'    pos base {gn(b)} <anchor {int(w * frac)} 0>'
                       f' mark @MC_{name};')
    if pos:
        lines.append('feature mark {\n' + '\n'.join(pos) + '\n} mark;')
    return '\n'.join(lines)


def add_missing_marks(glyphs):
    """דגש ונקודות שי"ן קיימים בגופן המקורי רק בתוך צורות מורכבות
    (בּ, שׁ, תּ...) ולא כגליף עצמאי. בלי ערך ב-cmap הדפדפן נופל לגופן
    חלופי בדיוק על האותיות האלה — לכן מוסיפים להם גליף ריק ברוחב אפס,
    ופיצ'ר ccmp מחליף את הרצף בגליף המורכב המקורי."""
    need = set()
    for seq, pre in PRECOMPOSED.items():
        if pre in glyphs:
            need.update(ch for ch in seq if ch not in glyphs)
    if not need:
        return
    blank = T2CharStringPen(0, None).getCharString()
    for ch in need:
        glyphs[ch] = (blank, 0, None)


class _DummyPrivate:
    """גליפים שנבנו ע"י T2CharStringPen חסרים הקשר Private, ובלעדיו
    draw() נופל. הערכים אינם משפיעים על קווי-המתאר עצמם."""
    nominalWidthX = 0
    defaultWidthX = 0


def contours_of(charstring):
    """מפרק גליף לקווי-מתאר נפרדים."""
    if getattr(charstring, 'private', None) is None:
        charstring.private = _DummyPrivate()
    rp = RecordingPen()
    charstring.draw(rp)
    out, cur = [], []
    for op, args in rp.value:
        cur.append((op, args))
        if op in ('closePath', 'endPath'):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _sig(contour):
    return tuple((op, tuple(tuple(round(v, 1) for v in pt) for pt in args))
                 for op, args in contour)


def strip_inner_mark(glyphs, base, key):
    """אות שיש לה צורה מנוקדת אחת בלבד (למשל סּ) — מסירים את סימן הדגש,
    שהוא קו-מתאר קטן ומבודד בתוך גוף האות."""
    cs = contours_of(glyphs[key][0])
    if len(cs) < 2:
        return False
    areas = []
    for c in cs:
        pts = [pt for op, args in c for pt in args]
        if not pts:
            areas.append((0, c))
            continue
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        h = max(p[1] for p in pts) - min(p[1] for p in pts)
        areas.append((w * h, c))
    areas.sort(key=lambda t: t[0])
    total = max(a for a, _ in areas)
    if not total or areas[0][0] > 0.12 * total:
        return False        # אין קו-מתאר קטן מספיק כדי להיות דגש
    pen = T2CharStringPen(glyphs[key][1], None)
    bp = BoundsPen(None)
    for _, c in areas[1:]:
        for op, args in c:
            getattr(pen, op)(*args)
            if hasattr(bp, op):
                getattr(bp, op)(*args)
    glyphs[base] = (pen.getCharString(), glyphs[key][1], bp.bounds)
    return True


def derive_base_letters(glyphs):
    """אותיות שבגופן המקורי מופיעות רק בצורה מנוקדת (למשל ך, שתמיד עם
    שווא או קמץ) — האות עצמה נבנית מקווי-המתאר המשותפים לשתי הצורות:
    מה שמשותף הוא האות, ומה שנבדל הוא הניקוד."""
    from collections import defaultdict
    # פירוק הפוך: לכל Presentation Form — האות והניקוד שממנו הורכב
    decomp = {v: k for k, v in PRECOMPOSED.items()}
    by_base = defaultdict(list)
    for key in list(glyphs):
        if len(key) == 2 and key[0] in HEBREW and key[1] in NIKUD:
            by_base[key[0]].append(key)
        elif len(key) == 1 and key in decomp and decomp[key][0] in HEBREW:
            by_base[decomp[key][0]].append(key)
    for base, keys in by_base.items():
        if base in glyphs or not keys:
            continue
        if len(keys) < 2:
            strip_inner_mark(glyphs, base, keys[0])
            continue
        sets = []
        for k in keys:
            cs = contours_of(glyphs[k][0])
            sets.append({_sig(c): c for c in cs})
        common = set(sets[0])
        for s in sets[1:]:
            common &= set(s)
        if not common:
            strip_inner_mark(glyphs, base, keys[0])
            continue
        pen = T2CharStringPen(glyphs[keys[0]][1], None)
        bp = BoundsPen(None)
        for s in common:
            for op, args in sets[0][s]:
                getattr(pen, op)(*args)
                if hasattr(bp, op):
                    getattr(bp, op)(*args)
        glyphs[base] = (pen.getCharString(), glyphs[keys[0]][1], bp.bounds)


def build_font(family_name, glyphs, out_dir):
    """בונה OTF + woff2 ממילון char → (charstring, width, bounds)."""
    if any(len(c) == 1 and c in NIKUD for c in glyphs):
        derive_base_letters(glyphs)
        add_missing_marks(glyphs)
    # הצורות המורכבות שימשו לחילוץ האותיות; הן עצמן אינן ניתנות למיפוי
    # ב-cmap (רצף של שני תווים), והטקסט מציג אותן כאות + סימן ניקוד
    for k in [k for k in glyphs if len(k) != 1]:
        del glyphs[k]
    order = ['.notdef'] + [f'uni{ord(c):04X}' for c in sorted(glyphs)]
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(c): f'uni{ord(c):04X}' for c in glyphs})

    pen = T2CharStringPen(None, None)
    notdef = pen.getCharString()
    charstrings = {'.notdef': notdef}
    metrics = {'.notdef': (250, 0)}
    ymin, ymax = 0, 0
    for c, (chstr, width, bounds) in glyphs.items():
        g = f'uni{ord(c):04X}'
        charstrings[g] = chstr
        lsb = bounds[0] if bounds else 0
        # סימן ניקוד = רוחב אפס, כדי שיצטרף לאות ולא יתפוס מקום
        adv = 0 if c in NIKUD else max(1, int(width or 0))
        metrics[g] = (adv, int(lsb))
        if bounds:
            ymin = min(ymin, bounds[1])
            ymax = max(ymax, bounds[3])
    fb.setupCFF(family_name, {'FamilyName': family_name,
                              'FullName': family_name}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    # מטריקות אנכיות אחידות לכל המשפחות: המנוע ממקם כל ריצה כך שה-baseline
    # יושב 0.86×גודל מראש הקופסה (עם line-height של 1.08). כשה-ascent/descent
    # של הפונט זהים לערכים אלה, הדפדפן מניח את הדיו בדיוק במקום המקורי —
    # לכל פונט, כולל פונט הקישוט שגבולות הדיו שלו זעירים.
    asc, desc = 860, -220
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    fb.setupNameTable({'familyName': family_name, 'styleName': 'Regular',
                       'fullName': family_name, 'psName': family_name})
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=asc, usWinDescent=-desc,
                fsSelection=0x40 | 0x80)
    fb.setupPost()
    fea = nikud_features(glyphs)
    if fea:
        from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
        addOpenTypeFeaturesFromString(fb.font, fea)
    out_dir.mkdir(parents=True, exist_ok=True)
    fb.font.flavor = 'woff2'
    path = out_dir / f'{family_name}.woff2'
    fb.font.save(str(path))
    # גרסת OTF להתקנה במערכת ההפעלה (מק/ווינדוס)
    otf_dir = out_dir.parent / 'fonts-install'
    otf_dir.mkdir(parents=True, exist_ok=True)
    fb.font.flavor = None
    fb.font.save(str(otf_dir / f'{family_name}.otf'))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--masechta', default='0,3,7,12,20',
                    help='רשימת מסכתות מופרדת בפסיקים — קצירה ממגוון דפים '
                         'מבטיחה כיסוי מלא גם של סימני פיסוק נדירים')
    ap.add_argument('--pages', type=int, default=40)
    ap.add_argument('--out', default=str(Path(__file__).parent / 'demo' / 'fonts'))
    args = ap.parse_args()

    candidates = {b: [] for b in FAMILIES}
    ttf_store = {}
    pages_read = 0
    for mas in args.masechta.split(','):
        for pg in range(args.pages):
            js = D.SHAS_DIR / mas.strip() / f'{pg}.js'
            if not js.exists():
                continue
            try:
                doc = pymupdf.open(stream=D.load_pdf(js), filetype='pdf')
            except Exception:
                continue
            harvest_page(doc, doc[0], candidates)
            harvest_ttf_page(doc, doc[0], ttf_store)
            pages_read += 1
    print(f'read {pages_read} pages; candidate subsets: '
          + ', '.join(f'{FAMILIES[b]}={len(candidates[b])}' for b in FAMILIES))

    # בפונט המנוקד (תורה אור) עדיף כיסוי מלא של האותיות על פני אחידות
    # חיתוך: הוא מופיע במעט מאוד טקסט, ואות חסרה בולטת הרבה יותר
    store = {b: merge_candidates(candidates[b], strict=(b != 'to'))
             for b in FAMILIES}
    # הוספת גליף רווח ברוחב שנמדד מה-PDF
    blank = T2CharStringPen(0, None).getCharString()
    for b in FAMILIES:
        widths = sorted(candidates.get('_space_' + b, []))
        if widths and store[b]:
            store[b][' '] = (blank, widths[len(widths) // 2], None)
    for b, fam in store.items():
        heb = sorted(c for c in fam if c in HEBREW)
        missing = sorted(HEBREW - set(fam))
        print(f'{FAMILIES[b]:12} {len(fam):3} glyphs | hebrew {len(heb)}/27'
              + (f' | missing: {"".join(missing)}' if missing else ''))
    out_dir = Path(args.out)
    for b, fam in store.items():
        if fam:
            path = build_font(FAMILIES[b], fam, out_dir)
            print('wrote', path)
    for fam, data in sorted(ttf_store.items()):
        heb = len([c for c in data['glyphs'] if c in HEBREW])
        print(f'{fam:22} {len(data["glyphs"]):3} glyphs | hebrew {heb}/27')
        path = build_ttf_font(fam, data, out_dir)
        if path:
            print('wrote', path)


if __name__ == '__main__':
    main()
