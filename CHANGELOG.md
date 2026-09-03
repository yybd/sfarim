# Changelog / יומן גרסאות

All notable, user-facing changes to **ספרים / Sfarim**. Newest version first.
Internal refactors and build plumbing are not listed here — only what changed for
the person using the app.

The newest entry is also what gets published as the Sparkle release notes and, if
the app ever ships to the App Store, as the release notes for that version.

---

## v1.0.2 — הגופנים של הש״ס החדש

**Fixed**
- **The ש״ס חדש pages are back in their own fonts.** The whole Talmud was rendering
  in the default system font — the gemara not in כתב וילנא, Rashi and Tosafot not in
  כתב רש״י. The viewer adopted only the daf itself out of each page file and dropped
  the `<style>` blocks that came with it, and those blocks are where the newer pages
  declare their fonts. Nothing on the page ever asked for the Talmud fonts, so none
  of them loaded.

---

## v1.0.1 — ש״ס חדש (טקסט חי בצורת הדף)

**Added**
- **ש״ס חדש** — a second Talmud library, reachable from a green button on the home
  screen. Every one of the 5,513 dapim is now real, live HTML text laid out in exact
  צורת הדף, instead of a page image: the Vilna page form is reproduced run by run at
  the original coordinates, in the original fonts extracted from the source.
- **Selectable, searchable text** — the daf lives in the page itself, so text can be
  selected with the mouse, found with Cmd+F, and printed. Copying yields one
  continuous line — no line breaks and no glued words.
- **Zones and segments** — gemara, Rashi, Tosafot, the margins and the header are
  identified per page, and each Rashi/Tosafot דיבור המתחיל is a whole selectable
  segment. Clicking a segment highlights it.
- **Crisp at any zoom** — the daf is re-rendered at the target size rather than
  scaled as an image, so letters stay sharp however far you zoom in. The `+` and `-`
  keys zoom as well, alongside the toolbar buttons.
- **Open-book look** — the daf curves gently into the binding and the edge of the
  facing page shows alongside it, full height, on the correct side for עמוד א / ב.
- **Tractate picker on the page** — the toolbar now carries the name of the open
  tractate with a caret; clicking it opens the picker. It sits centred above the
  daf instead of hiding behind a book icon, so the tractate you are in is always
  visible. The six סדרים are told apart in the picker by letter weight.

**Fixed**
- **The daf toolbar no longer stacks** — the zoom buttons used to fall onto a
  second line on narrow windows, costing half the toolbar's height.
- Commentary segments that disappeared with the eye button, column-detection and
  bottom-strip errors on a number of dapim, and reference markers swallowed into
  the דיבור המתחיל.

---

## v1.0.0 — first public release

*Released 2026-08-13 · macOS 11+ · **Apple Silicon only** · direct download*

First public, distributable build. Everything below shipped in it.

**Added**
- **Four libraries in one app** — תנ"ך, משנה, תלמוד בבלי and רמב"ם, all reachable
  from a single home screen.
- **Fully offline** — every text is packaged inside the app. No network access, no
  account, no tracking.
- **Safari-style tabs** — several texts open at once, switching between them without
  reloading; tab titles follow the page being viewed.
- **Immersive window** — opens maximized and without window chrome, so the page is
  the whole surface.
- **Automatic updates** — Sparkle checks for new versions on launch and once a day,
  and the ⟳ button in the tab bar runs a check on demand.

**Distribution**
- Signed with Developer ID, notarized by Apple and stapled — both the `.app` and the
  `.dmg`, so the app opens with no Gatekeeper warning.
- Published to Cloudflare R2 under a permanent link:
  <https://storage.bdtech.app/sfarim/releases/Sfarim.dmg>

**Not tracked here**
- Earlier in-repo builds (`0.1.0`, tagged `v0.11`) were development builds that were
  never distributed. Their history is not reconstructed.
