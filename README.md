# sfarim

A Tauri-based desktop application that wraps legacy Tanach and Mishna web applications, providing a modern desktop experience with enhanced features.

## Features

- **Tauri v2 & React**: Built with performance and security in mind.
- **Safari-style Tabs**: Browser-like tabbed interface for managing multiple pages.
- **Dynamic Titles**: Tabs automatically update their titles based on the content of the loaded pages.
- **Maximized Experience**: Launches in a maximized window without standard title bar decorations for an immersive view.
- **Legacy Support**: Seamlessly integrates existing HTML/JS content.

## Development

### Prerequisites

- Node.js
- pnpm (recommended)
- Rust (for Tauri)

### Setup

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Run the development server:
   ```bash
   pnpm tauri dev
   ```
   This command starts the frontend dev server and the Tauri application window.

3. Frontend only (no Tauri):
   ```bash
   pnpm dev
   ```

## Build

To build the application for production:

```bash
pnpm tauri build
```

The build artifacts will be available in `src-tauri/target/release/bundle`.
