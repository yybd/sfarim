# Changelog / יומן גרסאות

All notable, user-facing changes to **ספרים / Sfarim**. Newest version first.
Internal refactors and build plumbing are not listed here — only what changed for
the person using the app.

The newest entry is also what gets published as the Sparkle release notes and, if
the app ever ships to the App Store, as the release notes for that version.

---

## v1.0.0 — first public release

*Released 2026-08-13 · macOS 11+ (Apple Silicon) · direct download*

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
