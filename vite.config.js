import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from '@tailwindcss/vite';
import { rm } from 'node:fs/promises';
import { resolve } from 'node:path';

const host = process.env.TAURI_DEV_HOST;

// תיקיות ב-public/ שאינן נארזות לאפליקציה. הש"ס הישן (846MB של PDF)
// הוחלף בש"ס החדש כ-HTML, ואין טעם לשאת את שניהם בבאנדל.
// הן עדיין זמינות בשרת הפיתוח — רק לא בבנייה.
const EXCLUDE_FROM_BUNDLE = ['shas'];

function excludePublicDirs() {
  return {
    name: 'exclude-public-dirs',
    apply: 'build',
    async closeBundle() {
      for (const dir of EXCLUDE_FROM_BUNDLE) {
        await rm(resolve('dist', dir), { recursive: true, force: true });
      }
    },
  };
}

// https://vite.dev/config/
export default defineConfig(({
  plugins: [react(), tailwindcss(), excludePublicDirs()],
  base: "./",

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
        protocol: "ws",
        host,
        port: 1421,
      }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
  },
  envPrefix: ['VITE_', 'TAURI_ENV_*'],
  build: {
    // Tauri uses Chromium on Windows and WebKit on macOS and Linux
    target:
      process.env.TAURI_ENV_PLATFORM == 'windows'
        ? 'chrome105'
        : 'safari13',
    // don't minify for debug builds
    minify: !process.env.TAURI_ENV_DEBUG ? 'esbuild' : false,
    // produce sourcemaps for debug builds
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },

}));
