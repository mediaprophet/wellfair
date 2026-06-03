import init, * as wasm from '../docs/pkg/wellfare_core.js';

async function loadWasm() {
  try {
    await init();
    console.log('WASM initialized');
  } catch (e) {
    console.error('WASM load failed', e);
  }
}

loadWasm();

const fileInput = document.getElementById('fileInput');
const parseBtn = document.getElementById('parseBtn');
const output = document.getElementById('output');
const csvType = document.getElementById('csvType');

parseBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    output.textContent = 'No file selected';
    return;
  }
  const text = await file.text();
  const type = csvType.value;
  try {
    let result;
    if (type === 'weight') {
      result = wasm.weight_turtle_from_csv(text);
    } else if (type === 'sleep') {
      result = wasm.sleep_turtle_from_csv(text);
    } else if (type === 'hr') {
      result = wasm.heart_rate_turtle_from_csv(text);
    } else if (type === 'steps') {
      result = wasm.steps_turtle_from_csv(text);
    }
    output.textContent = await result;
  } catch (e) {
    output.textContent = 'Error: ' + e;
  }
});
