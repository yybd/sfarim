# Changelog / יומן גרסאות

All notable, user-facing changes to **ספרים / Sfarim**. Newest version first.
Internal refactors and build plumbing are not listed here — only what changed for
the person using the app.

The newest entry is also what gets published as the Sparkle release notes and, if
the app ever ships to the App Store, as the release notes for that version.

---

## Unreleased — ש״ס חדש (טקסט חי בצורת הדף)

*Built locally and installed for testing. Not published — no version bump, no
Sparkle release.*

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
