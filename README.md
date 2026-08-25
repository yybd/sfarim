# ספרים

A macOS desktop reader that bundles Tanach, Mishna, Talmud Bavli and Rambam into one
offline, tabbed library — no internet connection required.

- **App name:** ספרים (bundle / file name: `Sfarim`)
- **App Store name:** _not decided yet — direct download only for now_
- **Subtitle:** _not decided yet_
- **Platform:** macOS 11+ (Apple Silicon)
- **Bundle id:** `com.yybd.sfarim`
- **Built with:** Tauri v2 (Rust) + React 19, fully offline
- **Distribution:** direct download — Developer ID signed, notarized and stapled DMG
- **Updates:** Sparkle, appcast at `https://storage.bdtech.app/sfarim/releases/appcast.xml`

### 📥 Download / הורדה

**<https://storage.bdtech.app/sfarim/releases/Sfarim.dmg>** — a permanent link that
stays valid across versions. ~550 MB (the entire library ships inside the app).

> **Apple Silicon only** · **למחשבי Apple Silicon בלבד (M1 ומעלה)**
> The build is arm64-only, so it will not launch on an Intel Mac — Rosetta
> translates x86 to ARM, not the other way round. **Anywhere this link is
> published, that requirement has to be stated next to it.**
>
> This is a deliberate choice, not an oversight: because the library is compiled
> into the binary (see [Bundle size](#bundle-size--גודל-האפליקציה)), a universal
> build would carry the content twice and push the download to ~1.1 GB for every
> user. Revisit it if the content ever moves out of the binary.

**ספרים** היא אפליקציית דסקטופ ל-macOS המאגדת תנ"ך, משנה, תלמוד בבלי ורמב"ם בממשק לשוניות (טאבים)
בסגנון ספארי. כל התוכן ארוז בתוך האפליקציה — הלימוד עובד לגמרי ללא אינטרנט.

---

**Version 1.0.0** · First public release — direct download
Full history: [CHANGELOG.md](CHANGELOG.md)

## Features / תכונות

- **Four libraries in one app**: Tanach, Mishna, Talmud Bavli and Rambam, opened from a single home screen.
- **Fully offline**: every text ships inside the app — no network access, no account, no tracking.
- **Safari-style Tabs**: Manage multiple texts and pages simultaneously with a clean, intuitive tab interface.
- **Dynamic Titles**: Tabs automatically update their names based on the content being viewed.
- **Immersive View**: Launches in generalized full-screen mode to remove distractions.
- **Automatic updates**: Sparkle checks for new versions in the background; ⟳ in the tab bar checks on demand.
- **Modern Architecture**: Powered by Rust (Tauri) and React for high performance and security.

---

- **ארבע ספריות באפליקציה אחת**: תנ"ך, משנה, תלמוד בבלי ורמב"ם — הכול ממסך בית אחד.
- **עובד לגמרי לא מקוון**: כל הטקסטים ארוזים בתוך האפליקציה — בלי אינטרנט, בלי חשבון, בלי מעקב.
- **לשוניות בסגנון ספארי**: ניהול מספר טקסטים במקביל עם ממשק טאבים נקי ואינטואיטיבי.
- **כותרות דינמיות**: שמות הטאבים מתעדכנים אוטומטית בהתאם לתוכן הנצפה.
- **חוויה אימרסיבית**: האפליקציה נפתחת בחלון מקסימלי למיקוד בתוכן.
- **עדכונים אוטומטיים**: Sparkle בודק גרסאות חדשות ברקע; כפתור ⟳ בשורת הלשוניות בודק ביוזמת המשתמש.
- **ארכיטקטורה מודרנית**: מבוסס על Rust (Tauri) ו-React לביצועים גבוהים ואבטחה.

---

## Technical Architecture / ארכיטקטורה טכנית

The application is structured as a hybrid desktop app:

1.  **Backend (Rust/Tauri)**: Handles the native window creation, file system interactions (if any), and system-level events.
2.  **Frontend (React)**:
    -   **App.jsx**: The core layout manager. It implements a custom tab system where each tab state is preserved.
    -   **Tabs Logic**: Tabs are not browser windows but rendered `<iframe>` elements managed by React state. This allows for instant switching without reloading legacy content.
    -   **Iframe Isolation**: Legacy content loads inside sandboxed iframes, ensuring style isolation and stability.
    -   **Title Observer**: A `MutationObserver` attaches to each iframe to sync the tab title with the inner document's `<title>`.
3.  **Entry Point**: The default new tab loads `home.html` from the `public` directory.

### Bundle size / גודל האפליקציה

The whole library (`public/`, ~900 MB, of which `public/shas` is ~846 MB) is compiled
**into the Rust binary** — `Contents/MacOS/app` is ~580 MB while `Contents/Resources`
is under a megabyte. That is what makes the app fully offline, and it is also why the
download is ~550 MB and why **every** update is a full re-download regardless of how
small the change is. Moving the content into `bundle.resources` would shrink the
binary to ~10 MB and make incremental updates small; it would require the iframes to
load from a resource path instead of the embedded frontend.

### Updates / עדכונים

Sparkle is wired in through
[`tauri-plugin-sparkle-updater`](https://github.com/ahonn/tauri-plugin-sparkle-updater),
with `Sparkle.framework` 2.8.1 bundled into the app:

- Configured entirely from `src-tauri/Info.plist` — `SUFeedURL`, `SUPublicEDKey`,
  a check on launch and every 24 h, and **no** silent install (the user confirms).
- Updates are verified with an **EdDSA (ed25519)** signature. The key is the
  studio-wide one shared with the other direct-download apps (Iconduit, Snippet,
  the Office Tabs family), kept outside this repo at
  `~/Developer/myData/Sparkle/sparkle_private_key.txt`.
- `src-tauri/.cargo/config.toml` points the plugin's build script at the framework
  and adds the `@executable_path/../Frameworks` rpath it needs at runtime.
- Sparkle is macOS-only: the Cargo dependency, the plugin registration in `lib.rs`,
  and `capabilities/sparkle.json` are all platform-gated, so iOS builds are untouched.
- It does **not** run under `pnpm tauri dev` — Sparkle needs a real `.app` bundle.

---

## Development / פיתוח

### The Talmud viewer is a submodule / מציג הש"ס הוא submodule

`public/shas-hadash` is **not part of this repo**. It is a git submodule of
[yybd/shas-hadash](https://github.com/yybd/shas-hadash) — the single source of
truth for the Vilna-layout Talmud viewer (pages, `daf.js` logic, commentaries),
shared with the `talmud-ai` project.

**Never edit it here.** All viewer work happens in `talmud-ai`
(`~/Developer/AI/talmud-ai/public/shas-hadash`), which is the working repo.
sfarim only consumes what has already been pushed:

```bash
git submodule update --remote public/shas-hadash
git add public/shas-hadash && git commit -m "עדכון הש\"ס" && git push
```

After that the submodule sits in **detached HEAD** — that is correct and
intended here: it is the marker that sfarim is a consumer, not an editing site.

If `git status` shows `M public/shas-hadash` when you changed nothing, the
working tree has drifted from the recorded pointer. Resync with:

```bash
git submodule update --init --recursive public/shas-hadash
```

מציג הש"ס הוא submodule ממקור אמת משותף. **לא עורכים אותו כאן** — כל עריכה
נעשית ב-talmud-ai, וכאן רק מושכים. הנוהל המלא מתועד ב-README של
[shas-hadash](https://github.com/yybd/shas-hadash).

### Prerequisites / דרישות קדם

- Node.js
- pnpm (recommended)
- Rust (for Tauri build)
- Clone with `git clone --recurse-submodules` (or run `git submodule update --init`
  after a plain clone) — otherwise `public/shas-hadash` is an empty directory and
  the build fails.

### Setup / התקנה

1.  **Install dependencies / התקנת תלויות**:
    ```bash
    pnpm install
    ```

2.  **Run Development Server / הרצת שרת פיתוח**:
    ```bash
    pnpm tauri dev
    ```
    This launches both the Vite frontend server and the Tauri application window.
    פקודה זו מריצה את שרת ה-Frontend ופותחת את חלון האפליקציה.

3.  **Frontend Only / פיתוח פרונטנד בלבד**:
    ```bash
    pnpm dev
    ```
    Opens the interface in your minimal default browser (no native APIs).
    פותח את הממשק בדפדפן הרגיל (ללא יכולות native של Tauri).

### Build / בנייה לפרדוקשן

```bash
pnpm tauri build
```

Artifacts go to `src-tauri/target/release/bundle`. This produces an **unsigned**
build — for development only. For anything you hand to another person, use the
release flow below.

---

## Release / שחרור גרסה

Releasing is two commands. Bump `version` in `src-tauri/tauri.conf.json` (and
`src-tauri/Cargo.toml`) first, and add the new entry at the top of
[CHANGELOG.md](CHANGELOG.md).

```bash
./scripts/release-macos.sh    # build → sign → notarize → staple → sign appcast
./scripts/publish-r2.sh       # upload DMG + appcast to R2
```

Existing users get the update automatically within a day.

### The scripts / הסקריפטים

| Script | What it does |
|--------|--------------|
| `scripts/fetch-sparkle.sh` | Downloads Sparkle 2.8.1 into `src-tauri/Frameworks/` (checksum-pinned). Run **once per clone** — the framework is gitignored because this repo is public. |
| `scripts/sign-sparkle.sh` | Re-signs Sparkle with our Developer ID, inside out. Run automatically by the release script. |
| `scripts/release-macos.sh` | The full release build. Releases are deliberately arm64-only — `--universal` adds Intel but doubles the download; read the note under [Download](#-download--הורדה) first. |
| `scripts/publish-r2.sh` | Publishes what's staged in `releases/` to Cloudflare R2. |

### What the release script does / מה הסקריפט עושה

1. Signs `Sparkle.framework` with Developer ID, hardened runtime and a secure
   timestamp — **inside out** (XPC services → `Updater.app` → `Autoupdate` → the
   framework). Tauri only signs the app itself and not the binaries nested inside a
   bundled framework, and Apple's notary service rejects the build without this.
2. Builds and bundles, signing with **Developer ID Application** + hardened runtime.
   Tauri notarizes and staples the `.app` during this step.
3. Signs, notarizes and staples the **`.dmg` as well** — Tauri does not, and without
   it the user still gets a Gatekeeper warning when opening the disk image.
4. Copies the DMG to `releases/Sfarim.dmg` and generates an EdDSA-signed
   `appcast.xml` next to it.
5. Verifies everything: `codesign --verify --deep --strict` (app *and* framework),
   `spctl -a -t exec`, and `stapler validate` on both the app and the DMG.

Credentials are never hardcoded — this repo is public. The signing identity, the
notarytool API key (issuer, key id, `.p8` path) and the Sparkle key are all read at
runtime from `~/Developer/app-hub/DATA.md` and `~/Developer/myData/Sparkle/`, and can
be overridden with `APPLE_API_*` / `SPARKLE_KEY` environment variables.

### Published layout / מבנה הפרסום

The DMG is always published under a **stable name**, so the download link never
changes between versions (same convention as the other direct apps — `SnippetBar.dmg`,
`Iconduit.dmg`):

```
apps/sfarim/releases/Sfarim.dmg               ← stable name: download link + appcast enclosure
apps/sfarim/releases/<version>/Sfarim-<v>.dmg ← versioned archive copy
apps/sfarim/releases/appcast.xml              ← Sparkle feed
```

Served from Cloudflare R2 at `https://storage.bdtech.app/sfarim/releases/`, uploaded
with `rclone` (multipart — the DMG is far past the single-request limit). The DMG is
uploaded **before** the appcast, so the feed never advertises a build that isn't
downloadable yet.
