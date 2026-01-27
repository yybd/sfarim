# Sfarim / ספרים

**Sfarim** is a modern desktop application that serves as a unified wrapper for legacy Tanach and Mishna web applications. Built with **Tauri v2** and **React**, it provides a robust, tabs-based browsing experience similar to Safari, optimized for performance and immersion.

**ספרים** היא אפליקציית דסקטופ מודרנית המאגדת ספריות ווב קיימות של תנ"ך ומשנה. האפליקציה נבנתה באמצעות **Tauri v2** ו-**React**, ומספקת חווית גלישה מבוססת לשוניות (טאבים) בסגנון ספארי, עם דגש על ביצועים וחווית משתמש עוטפת.

---

## Features / תכונות

- **Modern Architecture**: Powered by Rust (Tauri) and React for high performance and security.
- **Safari-style Tabs**: Manage multiple texts and pages simultaneously with a clean, intuitive tab interface.
- **Dynamic Titles**: Tabs automatically update their names based on the content being viewed.
- **Immersive View**: Launches in generalized full-screen mode to remove distractions.
- **Legacy Integration**: Seamlessly renders existing HTML/JS content within a modern container.

---

- **ארכיטקטורה מודרנית**: מבוסס על Rust (Tauri) ו-React לביצועים גבוהים ואבטחה.
- **לשוניות בסגנון ספארי**: ניהול מספר טקסטים במקביל עם ממשק טאבים נקי ואינטואיטיבי.
- **כותרות דינמיות**: שמות הטאבים מתעדכנים אוטומטית בהתאם לתוכן הנצפה.
- **חוויה אימרסיבית**: האפליקציה נפתחת בחלון מקסימלי למיקוד בתוכן.
- **אינטגרציה חלקה**: טעינת תוכן HTML/JS קיים בתוך מעטפת מודרנית.

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

---

## Development / פיתוח

### Prerequisites / דרישות קדם

- Node.js
- pnpm (recommended)
- Rust (for Tauri build)

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

To create the production application:
ליצירת קובץ ההתקנה הסופי:

```bash
pnpm tauri build
```

Artifacts will be output to: `src-tauri/target/release/bundle`
הקבצים ייווצרו בנתיב הנ"ל.
