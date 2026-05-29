/**
 * WellFair Device File System Bridge
 * 
 * Provides real file-system access for installed PWAs (especially Android Chrome/Edge).
 * Uses the File System Access API to let users point at folders where health apps
 * export data (Samsung Health, Google Fit, etc.).
 * 
 * Once a directory is granted, relevant files are read and injected into Pyodide's
 * virtual filesystem so the existing Python import pipeline can consume them.
 */

window.WellFairDeviceBridge = (function() {
  let currentDirectoryHandle = null;
  let pyodideInstance = null;

  function isFileSystemAccessSupported() {
    return 'showDirectoryPicker' in window;
  }

  function isInstalledPWA() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  async function requestDeviceDirectory(options = {}) {
    if (!isFileSystemAccessSupported()) {
      throw new Error('File System Access API not supported in this browser. Use the file picker fallback.');
    }

    try {
      const dirHandle = await window.showDirectoryPicker({
        mode: 'read',
        startIn: options.startIn || 'downloads'
      });

      currentDirectoryHandle = dirHandle;

      // Expose for the scan function in the injected UI
      window.WellFairDeviceBridge._currentHandle = dirHandle;

      // Try to persist permission
      const permission = await dirHandle.queryPermission({ mode: 'read' });
      if (permission === 'prompt') {
        await dirHandle.requestPermission({ mode: 'read' });
      }

      return {
        name: dirHandle.name,
        kind: 'directory'
      };
    } catch (err) {
      if (err.name === 'AbortError') {
        return null;
      }
      throw err;
    }
  }

  async function scanDirectoryForHealthData(dirHandle, maxDepth = 3) {
    const results = {
      directoryName: dirHandle.name,
      files: [],
      totalSize: 0
    };

    async function walk(handle, currentPath = '', depth = 0) {
      if (depth > maxDepth) return;

      for await (const [name, entry] of handle.entries()) {
        const fullPath = currentPath ? `${currentPath}/${name}` : name;

        if (entry.kind === 'file') {
          // Focus on common health export formats
          const isRelevant = /\.(csv|json|xml|txt)$/i.test(name) ||
                            name.toLowerCase().includes('health') ||
                            name.toLowerCase().includes('samsung') ||
                            name.toLowerCase().includes('fit') ||
                            name.toLowerCase().includes('export');

          if (isRelevant) {
            try {
              const file = await entry.getFile();
              results.files.push({
                name: file.name,
                relativePath: fullPath,
                size: file.size,
                lastModified: file.lastModified,
                type: file.type
              });
              results.totalSize += file.size;
            } catch (e) {
              console.warn('Could not read file:', fullPath, e);
            }
          }
        } else if (entry.kind === 'directory' && depth < maxDepth) {
          try {
            await walk(entry, fullPath, depth + 1);
          } catch (e) {
            console.warn('Could not enter directory:', fullPath);
          }
        }
      }
    }

    await walk(dirHandle);
    return results;
  }

  async function readAndInjectFiles(pyodide, selectedFiles = null) {
    if (!currentDirectoryHandle || !pyodide) {
      throw new Error('No directory selected or Pyodide not ready');
    }

    pyodideInstance = pyodide;

    const targetDir = '/device_data';
    try {
      pyodide.FS.mkdir(targetDir);
    } catch (e) {
      // Directory may already exist
    }

    const injected = [];

    async function processEntry(handle, relativePath) {
      if (handle.kind === 'file') {
        const file = await handle.getFile();
        
        // Only process files the user or our scan selected
        if (selectedFiles && !selectedFiles.includes(file.name)) {
          return;
        }

        const content = await file.text();
        const virtualPath = `${targetDir}/${file.name}`;

        pyodide.FS.writeFile(virtualPath, content, { encoding: 'utf8' });
        
        injected.push({
          name: file.name,
          virtualPath,
          size: file.size
        });
      } else if (handle.kind === 'directory') {
        for await (const [name, child] of handle.entries()) {
          await processEntry(child, `${relativePath}/${name}`);
        }
      }
    }

    // Walk and inject
    for await (const [name, entry] of currentDirectoryHandle.entries()) {
      await processEntry(entry, name);
    }

    return {
      injectedCount: injected.length,
      files: injected,
      virtualRoot: targetDir
    };
  }

  function getCurrentDirectory() {
    return currentDirectoryHandle ? { name: currentDirectoryHandle.name } : null;
  }

  // Expose for use from within Pyodide / Streamlit
  window.wellfairRequestDeviceDirectory = requestDeviceDirectory;
  window.wellfairScanDeviceData = scanDirectoryForHealthData;
  window.wellfairInjectDeviceFiles = readAndInjectFiles;

  return {
    isSupported: isFileSystemAccessSupported,
    isInstalledPWA,
    requestDeviceDirectory,
    scanDirectoryForHealthData,
    readAndInjectFiles,
    getCurrentDirectory
  };
})();

console.log('[WellFair] Device Bridge loaded. Supported:', window.WellFairDeviceBridge.isSupported());