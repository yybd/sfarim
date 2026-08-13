#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  let builder = tauri::Builder::default();

  // Sparkle auto-updates — direct-download macOS builds only.
  // Configured from Info.plist (SUFeedURL / SUPublicEDKey); a no-op outside a
  // real .app bundle, so `tauri dev` is unaffected.
  #[cfg(target_os = "macos")]
  let builder = builder.plugin(tauri_plugin_sparkle_updater::init());

  builder
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
