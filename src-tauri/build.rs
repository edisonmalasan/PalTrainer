fn main() {
    tauri_build::build();

    #[cfg(target_os = "windows")]
    {
        if std::env::var("TARGET")
            .map(|t| t.contains("gnu"))
            .unwrap_or(false)
        {
            let out_dir = std::env::var("OUT_DIR").unwrap();
            let manifest_xml = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
        type="win32"
        name="Microsoft.Windows.Common-Controls"
        version="6.0.0.0"
        processorArchitecture="*"
        publicKeyToken="6595b64144ccf1df"
        language="*"
      />
    </dependentAssembly>
  </dependency>
</assembly>
"#;
            let _ = std::fs::write(format!("{out_dir}/app.manifest"), manifest_xml);
            let _ = std::fs::write(format!("{out_dir}/manifest.rc"), "1 24 \"app.manifest\"\n");
            let res_path = format!("{out_dir}/manifest.o");
            let status = std::process::Command::new("windres")
                .current_dir(&out_dir)
                .args(["-i", "manifest.rc", "-o", "manifest.o"])
                .status();
            if let Ok(status) = status {
                if status.success() {
                    println!("cargo:rustc-link-arg={res_path}");
                }
            }
        }
    }
}
