/**
 * Device Sources UI Controller
 * Loaded by the Stlite PWA build. Provides the bottom bar for choosing
 * folders on the user's phone when the app is installed as a PWA.
 */
(function () {
  const bar = document.getElementById('device-sources-bar');
  const chooseBtn = document.getElementById('device-choose-folder');
  const statusEl = document.getElementById('device-status');
  const importBtn = document.getElementById('device-import-btn');

  if (!bar || !window.WellFairDeviceBridge) return;

  const bridge = window.WellFairDeviceBridge;

  function shouldShow() {
    return bridge.isInstalledPWA && bridge.isSupported();
  }

  if (shouldShow()) {
    bar.style.display = 'block';
  }

  let currentHandle = null;

  chooseBtn.addEventListener('click', async () => {
    try {
      statusEl.textContent = 'Opening folder picker...';
      const info = await bridge.requestDeviceDirectory({ startIn: 'downloads' });
      if (!info) {
        statusEl.textContent = 'Cancelled by user';
        return;
      }
      currentHandle = window.WellFairDeviceBridge._currentHandle;
      statusEl.textContent = `Connected: ${info.name}`;

      statusEl.textContent = `Scanning for health exports...`;
      const scan = currentHandle ? await bridge.scanDirectoryForHealthData(currentHandle) : { files: [] };

      if (scan.files && scan.files.length > 0) {
        statusEl.textContent = `${scan.files.length} relevant files found`;
        importBtn.style.display = 'inline-block';
        importBtn.dataset.files = JSON.stringify(scan.files.map(f => f.name));
      } else {
        statusEl.textContent = 'No health export files detected in this folder';
      }
    } catch (err) {
      console.error(err);
      statusEl.textContent = 'Error: ' + (err.message || err);
    }
  });

  importBtn.addEventListener('click', async () => {
    if (!currentHandle) return;

    importBtn.disabled = true;
    statusEl.textContent = 'Reading files into vault...';

    try {
      const py = window.pyodide;
      if (!py) {
        statusEl.textContent = 'Python runtime not ready yet. Try again in a moment.';
        importBtn.disabled = false;
        return;
      }

      const result = await bridge.readAndInjectFiles(py);
      statusEl.textContent = `✓ ${result.injectedCount} files imported to /device_data`;

      // Let the Streamlit app know new data is available
      window.WELLFAIR_LAST_DEVICE_IMPORT = result;

      setTimeout(() => {
        statusEl.textContent = 'Device data ready — use "Device Exports" in the app';
      }, 1200);
    } catch (err) {
      console.error(err);
      statusEl.textContent = 'Import failed: ' + err.message;
    } finally {
      importBtn.disabled = false;
    }
  });
})();