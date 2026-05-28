# GitHub Pages + WASM Deployment Requirements

## Current status

The repository currently has a GitHub Pages workflow that publishes the contents of `docs/` as a documentation site. That workflow is located at `.github/workflows/pages.yml`.

However, the project is not yet configured to deploy a real WebAssembly-based browser application to GitHub Pages. The current Pages deployment only serves documentation, not a WASM frontend.

## Goal

Enable a static website deployment on GitHub Pages that loads the shared Rust core (`wellfare-core`) compiled to WebAssembly and runs the app logic in the browser.

## Required pieces

1. `wellfare-core` WASM compilation
   - Add the `wasm32-unknown-unknown` target if not already installed.
   - Add `wasm-bindgen` support in `wellfare-core` to expose browser-friendly entry points.
   - Add a `Cargo.toml` feature set or workspace configuration for WebAssembly builds.
   - Implement exported functions for parsing Samsung Health exports and generating RDF from browser-provided data.

2. Browser frontend shell
   - Add a static web frontend directory, e.g. `web/`, `frontend/`, or `docs/` with HTML/JS/CSS.
   - The frontend must load the compiled WASM module and provide a file upload UI.
   - Example entry points: `parseHealthExport`, `generateTurtle`, `savePodFile`, `showSleepAnalytics`.
   - Include a minimal app shell, user instructions, and a static site layout.

3. WASM build pipeline
   - Use `wasm-pack build --target web --out-dir web/pkg` or `cargo build --target wasm32-unknown-unknown --release` followed by `wasm-bindgen`.
   - Optionally use `npm`, `pnpm`, or `yarn` if bundling JavaScript around the WASM package.
   - Ensure build artifacts are copied into the GitHub Pages deploy directory.

4. GitHub Pages deployment workflow
   - Update `.github/workflows/pages.yml` to build the WASM frontend before deployment.
   - The workflow should produce a static site directory, for example `docs/`, containing:
     - generated HTML/CSS/JS
     - compiled `.wasm` files
     - `pkg/` or frontend bundle output
   - Use `actions/upload-pages-artifact@v1` and `actions/deploy-pages@v1` as the final deployment steps.

5. Static hosting constraints
   - GitHub Pages only hosts static content, so the app must run fully in the browser.
   - All data ingestion, normalization, RDF generation, and analytics must execute client-side in the browser.
   - No server-side Python or Streamlit backend can be hosted on GitHub Pages.

## Recommended implementation path

1. Create a lightweight static frontend under `web/` or `docs/`.
2. Add `#[wasm_bindgen]` exports in `wellfare-core/src/lib.rs`.
3. Add `wasm-bindgen` and `js-sys`/`web-sys` dependencies to `wellfare-core/Cargo.toml`.
4. Add a build script or npm package script for producing static deploy files.
5. Update the GitHub Actions workflow so `docs/` contains the built site.

## Example build workflow steps

```yaml
- uses: actions/checkout@v4
- name: Install wasm-pack
  run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
- name: Build WASM package
  run: |
    cd wellfare-core
    wasm-pack build --target web --out-dir ../docs/pkg
- name: Copy web frontend
  run: |
    cp -r web/* docs/
- name: Upload Pages artifact
  uses: actions/upload-pages-artifact@v1
  with:
    path: docs
```

## Notes

- If the frontend uses a JS framework, the workflow must also install Node and build the frontend assets.
- The `docs/` folder can serve both documentation and the WASM app, but be careful to avoid overwriting generated assets.
- A separate GitHub Pages branch or `gh-pages` branch is optional if the current workflow is kept.

## Conclusion

The project is not yet set up to deploy a real WebAssembly app on GitHub Pages. The current workflow only deploys documentation. To complete the WASM deployment, add a browser frontend, WASM export surface, build pipeline, and an updated Pages workflow.
