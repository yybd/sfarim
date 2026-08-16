#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_all — ייצור כל דפי הש"ס כ-HTML בצורת הדף.

מבנה הפלט (ברירת מחדל: public/shas/daf):

    daf/
      assets/            daf.css, daf.js, fonts/*.woff2   (משותפים לכל הדפים)
      0/2.html.gz  0/3.html.gz ...                        (מסכת/עמוד, gzip)
      index.json                                          (מפת מה שנבנה)

כל דף מקשר ל-assets בנתיב יחסי, ולכן התיקייה כולה ניתנת להעברה כמו שהיא.

שימוש:
    python build_all.py [--out DIR] [--jobs N] [--masechta 0,3] [--dump-text]
"""
import argparse
import gzip
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import daf2html as D          # noqa: E402
import pymupdf                # noqa: E402

HERE = Path(__file__).parent
DEFAULT_OUT = HERE.parents[1] / 'public' / 'shas' / 'daf'


def write_gz(path, text):
    """כתיבה דחוסה ודטרמיניסטית (mtime=0 — אותו קלט → אותם ביטים)."""
    with open(path, 'wb') as f:
        with gzip.GzipFile(fileobj=f, mode='wb', compresslevel=9, mtime=0) as g:
            g.write(text.encode('utf-8'))


def build_page(args):
    """בונה דף בודד. רץ בתהליך נפרד — מחזיר סיכום קצר בלבד."""
    mas, page, out_dir, dump_text = args
    js = D.SHAS_DIR / mas / f'{page}.js'
    try:
        doc = pymupdf.open(stream=D.load_pdf(js), filetype='pdf')
        pg = doc[0]
        fixmaps = D.build_fixmaps(doc, pg)
        chars = D.extract_chars(pg, fixmaps)
        ttf = {f[3].split('+')[-1] for f in pg.get_fonts() if f[1] == 'ttf'}
        ftab = D.build_font_table(chars, ttf)
        lines = D.group_lines(chars, ftab)
        rashi_side = 'right' if int(page) % 2 == 0 else 'left'
        html = D.render_html(lines, pg.rect.width, pg.rect.height,
                             '../assets/fonts', f'{mas}/{page}',
                             rashi_side, '../assets')
        # אחסון דחוס — ה-HTML זהה ביט-ביט אחרי פריסה; ה-viewer פורס
        # בזמן טעינה עם DecompressionStream
        target = Path(out_dir) / mas / f'{page}.html.gz'
        target.parent.mkdir(parents=True, exist_ok=True)
        write_gz(target, html)
        size = target.stat().st_size

        if dump_text:
            gb = D.gemara_bbox(lines)
            D.assign_segments(lines, gb, rashi_side)
            # classify_lines — הסיווג המלא (יחס-גודל + הכלה בטור השוליים)
            zmap = D.classify_lines(lines, gb, rashi_side)
            zones, segs = {}, {}
            for ln in sorted(lines, key=lambda l: (l['y0'], -l['x1'])):
                z = zmap[id(ln)]
                t = ''.join(p['text'] + (' ' if p.get('sp') else '')
                            for p in ln['parts']).strip()
                if t and set(t) != {D.ORNAMENT}:
                    zones.setdefault(z, []).append(t)
                for p in ln['parts']:
                    if p.get('seg'):
                        e = segs.setdefault(p['seg'], {'dh': '', 'text': ''})
                        e['dh' if p.get('dh') else 'text'] += \
                            p['text'] + (' ' if p.get('sp') else '')
            txt = Path(out_dir) / 'text' / mas / f'{page}.json.gz'
            txt.parent.mkdir(parents=True, exist_ok=True)
            write_gz(txt, json.dumps({
                'zones': {z: ' '.join(ts) for z, ts in zones.items()},
                'segments': {s: {'dh': v['dh'].strip(), 'text': v['text'].strip()}
                             for s, v in segs.items()},
            }, ensure_ascii=False))
        return {'mas': mas, 'page': page, 'bytes': size, 'lines': len(lines)}
    except Exception as e:
        return {'mas': mas, 'page': page, 'error': f'{type(e).__name__}: {e}'}


def copy_assets(out_dir):
    assets = Path(out_dir) / 'assets'
    (assets / 'fonts').mkdir(parents=True, exist_ok=True)
    for name in ('daf.css', 'daf.js'):
        shutil.copy2(HERE / 'demo' / name, assets / name)
    names = []
    for f in sorted((HERE / 'demo' / 'fonts').glob('*.woff2')):
        shutil.copy2(f, assets / 'fonts' / f.name)
        names.append(f.stem)
    # גיליון @font-face משותף — לשימוש כשמזריקים דף לתוך מסמך אחר
    # (בהזרקה הנתיבים היחסיים שבתוך הדף אינם תקפים)
    (assets / 'fonts.css').write_text('\n'.join(
        "@font-face { font-family:'%s'; src:url('fonts/%s.woff2') format('woff2'); }"
        % (n, n) for n in names) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument('--masechta', default='', help='רשימה מופרדת בפסיקים; ריק = הכל')
    ap.add_argument('--dump-text', action='store_true',
                    help='ייצוא טקסט פר-אזור ופר-מקטע לאינדוקס חיפוש')
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(out_dir)

    wanted = set(args.masechta.split(',')) if args.masechta else None
    jobs = []
    for js in sorted(D.SHAS_DIR.glob('*/*.js')):
        mas, page = js.parent.name, js.stem
        if not mas.isdigit() or not page.isdigit():
            continue
        if wanted and mas not in wanted:
            continue
        jobs.append((mas, page, str(out_dir), args.dump_text))
    jobs.sort(key=lambda j: (int(j[0]), int(j[1])))

    print(f'בונה {len(jobs)} דפים ב-{args.jobs} תהליכים → {out_dir}', flush=True)
    t0 = time.time()
    done = failed = total_bytes = 0
    index, errors = {}, []
    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(build_page, j) for j in jobs]
        for fut in as_completed(futs):
            r = fut.result()
            done += 1
            if 'error' in r:
                failed += 1
                errors.append(r)
            else:
                total_bytes += r['bytes']
                index.setdefault(r['mas'], []).append(int(r['page']))
            if done % 250 == 0 or done == len(jobs):
                el = time.time() - t0
                rate = done / el if el else 0
                print(f'  {done}/{len(jobs)} ({el:.0f}s, {rate:.1f}/s) '
                      f'| שגיאות: {failed} | {total_bytes/1e6:.0f} MB', flush=True)

    for mas in index:
        index[mas].sort()
    (out_dir / 'index.json').write_text(json.dumps(
        {'pages': {m: index[m] for m in sorted(index, key=int)},
         'total': sum(len(v) for v in index.values())},
        ensure_ascii=False, indent=1))
    if errors:
        (out_dir / 'build-errors.json').write_text(
            json.dumps(errors, ensure_ascii=False, indent=1))

    el = time.time() - t0
    print(f'\n=== הסתיים ב-{el/60:.1f} דקות ===')
    print(f'  דפים שנבנו: {done - failed}/{len(jobs)}')
    print(f'  שגיאות: {failed}')
    print(f'  נפח HTML: {total_bytes/1e9:.2f} GB '
          f'(ממוצע {total_bytes/max(1, done-failed)/1024:.0f} KB לדף)')
    print(f'  פלט: {out_dir}')


if __name__ == '__main__':
    main()
