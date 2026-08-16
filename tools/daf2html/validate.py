#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate — בדיקת תקפות המנוע על פני כל דפי הש"ס.

לכל דף נבדקים:
  error        — חריגה בעיבוד (כשל קשה)
  ctrl         — תווי בקרה בטקסט (גליף שלא פוענח)
  noglyph      — תווים שאין להם גליף בגופן שהוקצה להם
  degenerate   — ריצות עם גיאומטריה פגומה (רוחב אפס/שלילי, NaN)
  heb_ratio    — שיעור העברית בטקסט (פענוח משובש מוריד אותו)
  no_gemara    — לא זוהה גוש גמרא (צפוי בעמודי שער/הדרן — אזהרה בלבד)
  unknown_fam  — משפחת גופן שאין לה קובץ woff2 (פונט חדש שטרם נקצר)

שימוש:  python validate.py [--sample N] [--out report.jsonl]
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import daf2html as D          # noqa: E402
import pymupdf                # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

FONTS_DIR = Path(__file__).parent / 'demo' / 'fonts'
FAM_FILE = dict(D.FAM_FILE)

HEB = re.compile(r'[֐-׿]')  # כולל ניקוד — דפים מנוקדים אינם חריגים


def load_coverage():
    cov = {}
    for f in glob.glob(str(FONTS_DIR / 'Shas*.woff2')):
        name = os.path.basename(f)[:-6]
        try:
            cov[name] = {chr(c) for c in TTFont(f).getBestCmap()}
        except Exception:
            pass
    return cov


def check_page(js_path, cov):
    rec = {'page': f'{js_path.parent.name}/{js_path.stem}'}
    try:
        doc = pymupdf.open(stream=D.load_pdf(js_path), filetype='pdf')
        page = doc[0]
        fixmaps = D.build_fixmaps(doc, page)
        chars = D.extract_chars(page, fixmaps)
        ttf = {f[3].split('+')[-1] for f in page.get_fonts() if f[1] == 'ttf'}
        ftab = D.build_font_table(chars, ttf)
        lines = D.group_lines(chars, ftab)
    except Exception as e:
        rec['error'] = f'{type(e).__name__}: {e}'
        return rec

    ctrl = noglyph = deg = heb = solid = 0
    unknown = set()
    for l in lines:
        for p in l['parts']:
            if not (p['x1'] > p['x0'] >= 0) or p['oy'] != p['oy']:
                deg += 1
            fam = p.get('fam', 'sq')
            fname = FAM_FILE.get(fam, fam)
            known = cov.get(fname)
            if known is None and fname != 'or':
                unknown.add(fname)
            for ch in p['text']:
                if ord(ch) < 0x20:
                    ctrl += 1
                elif ch.strip():
                    solid += 1
                    if HEB.match(ch):
                        heb += 1
                    if known is not None and ch not in known:
                        noglyph += 1
    rec.update(lines=len(lines), chars=solid, ctrl=ctrl, noglyph=noglyph,
               degenerate=deg)
    rec['heb_ratio'] = round(heb / solid, 3) if solid else 0.0
    gb = D.gemara_bbox(lines)
    rec['no_gemara'] = gb == (200, 450, 60, 700)
    if unknown:
        rec['unknown_fam'] = sorted(unknown)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', type=int, default=0,
                    help='בדוק כל דף N-י בלבד (0 = הכל)')
    ap.add_argument('--out', default=str(Path(__file__).parent / 'validate-report.jsonl'))
    args = ap.parse_args()

    cov = load_coverage()
    pages = sorted(D.SHAS_DIR.glob('*/*.js'),
                   key=lambda p: (int(p.parent.name), int(p.stem)))
    if args.sample:
        pages = pages[::args.sample]

    t0 = time.time()
    stats = {'pages': 0, 'errors': 0, 'ctrl_pages': 0, 'noglyph_pages': 0,
             'degenerate_pages': 0, 'low_heb': 0, 'no_gemara': 0,
             'unknown_fam_pages': 0}
    with open(args.out, 'w') as out:
        for i, js in enumerate(pages):
            rec = check_page(js, cov)
            stats['pages'] += 1
            if 'error' in rec:
                stats['errors'] += 1
            else:
                if rec['ctrl']:
                    stats['ctrl_pages'] += 1
                if rec['noglyph'] > rec['chars'] * 0.001:
                    stats['noglyph_pages'] += 1
                if rec['degenerate']:
                    stats['degenerate_pages'] += 1
                if rec['chars'] > 500 and rec['heb_ratio'] < 0.85:
                    stats['low_heb'] += 1
                if rec['no_gemara']:
                    stats['no_gemara'] += 1
                if rec.get('unknown_fam'):
                    stats['unknown_fam_pages'] += 1
            interesting = ('error' in rec or rec.get('ctrl') or
                           rec.get('degenerate') or rec.get('unknown_fam') or
                           rec.get('no_gemara') or
                           (rec.get('chars', 0) > 500 and rec.get('heb_ratio', 1) < 0.85) or
                           rec.get('noglyph', 0) > rec.get('chars', 1) * 0.001)
            if interesting:
                out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            if (i + 1) % 250 == 0:
                el = time.time() - t0
                print(f'{i+1}/{len(pages)} ({el:.0f}s) | {stats}', flush=True)
    print('=== סיכום ===')
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    print('דו"ח חריגים:', args.out)


if __name__ == '__main__':
    main()
