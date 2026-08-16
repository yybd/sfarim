/*
 * daf.js — כל הלוגיקה של דפי צורת-הדף, מחוץ לדפים עצמם.
 *
 * הדף שנוצר מכיל אך ורק גיאומטריה וטקסט: כל ריצת-טקסט ממוקמת אבסולוטית
 * לפי המיקום המדויק שלה ב-PDF. הקובץ הזה מוסיף בזמן ריצה את כל השאר —
 * סיווג לאזורים, פילוח לדיבורי-המתחיל, קיבוץ ה-DOM לפי אזור (כדי
 * שגרירה בעכבר תבחר טקסט של מקטע אחד בלבד), ואת ה-API לאפליקציה.
 * שיפור בלוגיקה נעשה כאן פעם אחת וחל על כל הדפים — בלי לייצר אותם מחדש.
 *
 * API — window.Daf:
 *   Daf.zones()               רשימת האזורים שנמצאו בדף
 *   Daf.zoneOf(el)            האזור של אלמנט
 *   Daf.zoneText(zone)        הטקסט הרציף של אזור
 *   Daf.segments()            מזהי כל המקטעים ('r3' / 't1')
 *   Daf.segText(segId)        הטקסט המלא של מקטע (ד"ה + גוף)
 *   Daf.select(segId)         בחירת/ביטול מקטע שלם; null מנקה
 *   Daf.selected()            מזהה המקטע הנבחר או null
 *   Daf.hide(zone) / show / toggle / hidden()
 *   Daf.fit()                 כיול רוחב הריצות (רץ אוטומטית)
 * אירוע: 'daf:select' על ה-document עם detail={seg}.
 */
(function () {
  'use strict';

  var ZONES = ['header', 'gemara', 'rashi', 'tosafot',
               'margin-right', 'margin-left', 'bottom'];
  var SQUARE = { 'sq': 1, 'sqs': 1, 'bd': 1, 'dh': 1, 'to': 1 };

  // גודל וסוג-כתב נגזרים מהריצה עצמה (font-size ומחלקת הגופן), כדי
  // שהדף לא יישא אותם שוב כ-data attributes בכל מילה
  function wsize(w) { return parseFloat(w.style.fontSize) || 0; }
  function wfam(w) {
    var m = /(?:^|\s)f-([\w-]+)/.exec(w.className);
    return m ? m[1] : 'sq';
  }
  function isSquare(w) {
    var f = wfam(w);
    if (SQUARE[f]) return true;
    if (f === 'rs' || f === 'rss') return false;
    return !/rashi/i.test(f);       // גופני TrueType — לפי שמם
  }

  function daf() { return document.querySelector('.daf-page'); }
  function num(el, k) { return parseFloat(el.dataset[k]); }

  // ---------------------------------------------------------- סיווג אזורים

  function gemaraMetrics(lines) {
    // הגמרא היא הכתב המרובע הגדול ביותר שיש לו נפח טקסט ממשי: השוליים
    // מרובעים אף הם אך קטנים בהרבה, והכותרות גדולות אך זעירות בנפחן.
    // סף גודל קבוע נשבר במסכתות שגופן הגמרא בהן קטן (מנחות — 11.5).
    var mass = {}, total = 0, cands = [];
    lines.forEach(function (ln) {
      if (parseFloat(ln.style.top) <= 28) return;
      var main = mainRun(ln);
      if (!main || !isSquare(main)) return;
      var n = 0;
      ln.querySelectorAll('.w').forEach(function (w) { n += w.textContent.length; });
      var k = num(ln, 'size').toFixed(1);
      mass[k] = (mass[k] || 0) + n;
      total += n;
      cands.push(ln);
    });
    var gsize = 0;
    Object.keys(mass).forEach(function (k) {
      if (mass[k] >= 0.10 * total) gsize = Math.max(gsize, parseFloat(k));
    });
    if (!gsize) return { box: { x0: 200, x1: 450, y0: 60, y1: 700 }, size: 13.7 };
    var x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    cands.forEach(function (ln) {
      if (Math.abs(num(ln, 'size') - gsize) >= 0.6) return;
      var top = parseFloat(ln.style.top);
      x0 = Math.min(x0, num(ln, 'x0')); x1 = Math.max(x1, num(ln, 'x1'));
      y0 = Math.min(y0, top); y1 = Math.max(y1, top + 1.08 * num(ln, 'size'));
    });
    return { box: { x0: x0, x1: x1, y0: y0, y1: y1 }, size: gsize };
  }

  function mainRun(ln) {
    var best = null;
    ln.querySelectorAll('.w').forEach(function (w) {
      if (!best || w.textContent.length > best.textContent.length) best = w;
    });
    return best;
  }

  function classify(ln, gb, rashiSide, gsize) {
    var x0 = num(ln, 'x0'), x1 = num(ln, 'x1'), top = parseFloat(ln.style.top);
    var cx = (x0 + x1) / 2, main = mainRun(ln), size = num(ln, 'size');
    if (top < 28) return 'header';
    if (size >= 0.9 * gsize && main && isSquare(main) &&
        cx >= gb.x0 - 10 && cx <= gb.x1 + 10) return 'gemara';
    if (top > gb.y1 + 8) return 'bottom';
    var inGemaraX = cx >= gb.x0 - 10 && cx <= gb.x1 + 10;
    if (gsize && size < 0.65 * gsize && !inGemaraX) {
      return cx > (gb.x0 + gb.x1) / 2 ? 'margin-right' : 'margin-left';
    }
    var right = cx > (gb.x0 + gb.x1) / 2;
    return (rashiSide === 'right') === right ? 'rashi' : 'tosafot';
  }

  // ------------------------------------------------ פילוח לדיבורי-המתחיל

  function bodySize(lines) {
    // גודל גוף הטקסט השכיח באזור (במשקל תווים)
    var acc = {};
    lines.forEach(function (ln) {
      ln.querySelectorAll('.w').forEach(function (w) {
        if (isSquare(w)) return;
        var k = wsize(w).toFixed(1);
        acc[k] = (acc[k] || 0) + w.textContent.length;
      });
    });
    var best = 11.2, bv = -1;
    Object.keys(acc).forEach(function (k) {
      if (acc[k] > bv) { bv = acc[k]; best = parseFloat(k); }
    });
    return best;
  }

  function dhState(w, lineSize, body) {
    // ד"ה: כתב מרובע בגודל שורה מלא, או כתב רש"י גדול מגוף האזור.
    // null = ניטרלי (פיסוק) וממשיך את המצב הקודם.
    if (!/[א-ת]/.test(w.textContent)) return null;
    var sz = wsize(w), sq = isSquare(w);
    if (sq && sz >= 0.95 * lineSize &&
        w.textContent.replace(/[^א-ת]/g, '').length >= 2) return true;
    if (!sq && sz >= body + 0.3) return true;
    return false;
  }

  var FAM_CLASSES = ['f-sq', 'f-sqs', 'f-rs', 'f-rss', 'f-dh', 'f-bd', 'f-to'];
  var TTF_FAM = /^f-Shas/;

  function segment(zoneLines, prefix, zone) {
    var body = bodySize(zoneLines), seg = 0, inDh = false;
    zoneLines.forEach(function (ln) {
      var lineSize = num(ln, 'size');
      ln.querySelectorAll('.w').forEach(function (w) {
        var dh = dhState(w, lineSize, body);
        if (dh === null) dh = inDh;
        else if (dh && !inDh) seg++;
        inDh = dh;
        w.dataset.seg = prefix + seg;
        if (!dh) return;
        w.classList.add('dh');
        // ד"ה של תוספות בכתב מרובע (וילנה) כמו בדפוס. ב-PDF הוא מקודד
        // כמו כתב רש"י ולכן הזיהוי לפי הקידוד לבדו מפספס אותו.
        if (zone === 'tosafot') {
          FAM_CLASSES.forEach(function (c) { w.classList.remove(c); });
          [].slice.call(w.classList).forEach(function (c) {
            if (TTF_FAM.test(c)) w.classList.remove(c);
          });
          w.classList.add('f-dh');
        }
      });
    });
  }

  // ------------------------------------- קיבוץ ה-DOM לפי אזור (לבחירה)

  function build() {
    var d = daf();
    if (!d || d.dataset.ready) return;
    var lines = Array.prototype.slice.call(d.querySelectorAll('.ln'));
    var gm = gemaraMetrics(lines);
    var gb = gm.box, gsize = gm.size;
    var side = d.dataset.rashiSide || 'right';
    var zoneOfLine = new Map();
    lines.forEach(function (ln) { zoneOfLine.set(ln, classify(ln, gb, side, gsize)); });
    // כותרות המדורים ("מסורת הש"ס", "תורה אור השלם") מודפסות בגופן גדול
    // מגוף המדור, ולכן מבחן הגודל מפספס אותן — מצרפים לפי הכלה בטור
    ['margin-left', 'margin-right'].forEach(function (side2) {
      var cols = lines.filter(function (l) { return zoneOfLine.get(l) === side2; });
      if (!cols.length) return;
      var lo = Math.min.apply(null, cols.map(function (l) { return num(l, 'x0'); })) - 2;
      var hi = Math.max.apply(null, cols.map(function (l) { return num(l, 'x1'); })) + 2;
      lines.forEach(function (l) {
        var z = zoneOfLine.get(l);
        if ((z === 'rashi' || z === 'tosafot') &&
            num(l, 'x0') >= lo && num(l, 'x1') <= hi) zoneOfLine.set(l, side2);
      });
    });
    var byZone = {};
    lines.forEach(function (ln) {
      var z = zoneOfLine.get(ln);
      ln.classList.add(z);
      (byZone[z] = byZone[z] || []).push(ln);
    });
    // סדר ה-DOM אינו משפיע על המיקום (הכל אבסולוטי), ולכן אפשר לקבץ
    // את השורות לפי אזור. כך גרירה בעכבר בתוך עמודה בוחרת רק אותה,
    // במקום לדלג בין הגמרא, רש"י ותוס' שיושבים באותו גובה.
    ZONES.forEach(function (z) {
      if (!byZone[z]) return;
      var box = document.createElement('div');
      box.className = 'zone zone-' + z;
      box.dataset.zone = z;
      byZone[z].sort(function (a, b) {
        var dy = parseFloat(a.style.top) - parseFloat(b.style.top);
        return dy || (num(b, 'x1') - num(a, 'x1'));
      }).forEach(function (ln) { box.appendChild(ln); });
      d.appendChild(box);
    });
    if (byZone.rashi) segment(byZone.rashi, 'r', 'rashi');
    if (byZone.tosafot) segment(byZone.tosafot, 't', 'tosafot');
    d.dataset.ready = '1';
  }

  // ---------------------------------------------------------------- API

  function runText(nodes) {
    var out = [];
    nodes.forEach(function (x) {
      out.push(x.textContent);
      var nx = x.nextSibling;
      if (nx && nx.nodeType === 3 && /\s/.test(nx.textContent)) out.push(' ');
    });
    return out.join('').trim();
  }

  var Daf = {
    ZONES: ZONES,
    // בנייה מחדש — לשימוש כשמזריקים דף חדש לאותו מסמך
    build: function () { build(); },

    fit: function () {
      var box = daf();
      if (!box) return;
      // מקדם התצוגה (zoom/scale של הדפדפן) — בלעדיו המדידה מוחזרת
      // ביחידות מסך ולא ביחידות הדף, וכל הריצות היו נדחסות
      var zoom = box.offsetWidth ?
        box.getBoundingClientRect().width / box.offsetWidth : 0;
      if (!isFinite(zoom) || zoom < 0.01) return;   // אי אפשר למדוד — לא נוגעים
      document.querySelectorAll('.w[data-w]').forEach(function (el) {
        el.style.transform = '';
        var want = parseFloat(el.dataset.w);
        var got = el.getBoundingClientRect().width / zoom;
        if (want > 0.5 && got > 0.5 && Math.abs(got - want) / want > 0.02) {
          el.style.transform = 'scaleX(' + (want / got) + ')';
        }
      });
    },

    zones: function () {
      return ZONES.filter(function (z) { return document.querySelector('.zone-' + z); });
    },
    zoneOf: function (el) {
      var z = el && el.closest ? el.closest('.zone') : null;
      return z ? z.dataset.zone : null;
    },
    zoneText: function (zone) {
      var box = document.querySelector('.zone-' + zone);
      if (!box) return '';
      return Array.prototype.slice.call(box.querySelectorAll('.ln'))
        .map(function (ln) {
          return runText(Array.prototype.slice.call(ln.querySelectorAll('.w')));
        }).join(' ');
    },

    segments: function () {
      var seen = [];
      document.querySelectorAll('[data-seg]').forEach(function (w) {
        if (seen.indexOf(w.dataset.seg) < 0) seen.push(w.dataset.seg);
      });
      return seen;
    },
    segText: function (segId) {
      return runText(Array.prototype.slice.call(
        document.querySelectorAll('[data-seg="' + segId + '"]')));
    },
    select: function (segId) {
      document.querySelectorAll('.seghl').forEach(function (x) {
        x.classList.remove('seghl');
      });
      if (segId) {
        document.querySelectorAll('[data-seg="' + segId + '"]')
          .forEach(function (x) { x.classList.add('seghl'); });
      }
      document.dispatchEvent(new CustomEvent('daf:select',
        { detail: { seg: segId || null } }));
    },
    selected: function () {
      var el = document.querySelector('.seghl');
      return el ? el.dataset.seg : null;
    },

    hide: function (z) { daf().classList.add('hide-' + z); },
    show: function (z) { daf().classList.remove('hide-' + z); },
    toggle: function (z) { daf().classList.toggle('hide-' + z); },
    hidden: function () {
      return ZONES.filter(function (z) {
        return daf().classList.contains('hide-' + z);
      });
    },
  };

  document.addEventListener('click', function (e) {
    var seg = e.target.dataset && e.target.dataset.seg;
    if (!seg || !window.getSelection().isCollapsed) return;   // לא בזמן גרירה
    Daf.select(Daf.selected() === seg ? null : seg);
  });

  // העתקה: הדפדפן מכניס שבירת-שורה בין שורות הדף (כל שורה היא div).
  // כשהבחירה בתוך הדף — מנרמלים לקטע רציף אחד: כל רצף רווחים/שבירות
  // הופך לרווח בודד. חל רק על בחירה בתוך .daf-page, לא על שאר האפליקציה.
  document.addEventListener('copy', function (e) {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !e.clipboardData) return;
    var node = sel.anchorNode;
    var el = node && (node.nodeType === 1 ? node : node.parentElement);
    if (!el || !el.closest('.daf-page')) return;
    e.clipboardData.setData('text/plain',
      sel.toString().replace(/\s+/g, ' ').trim());
    e.preventDefault();
  });

  build();
  document.fonts.ready.then(Daf.fit);
  window.Daf = Daf;
}());
