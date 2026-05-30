// text.linguistic Worker — pronoun density, sentiment, coherence, hedge ratio
//
// Module key: 'text.linguistic'
// Loaded by:  vault-cv.js via new Worker('js/workers/text-linguistic.worker.js')
//             Classic worker (not module). Pure JS — no external libraries.
//
// Input:  postMessage({ text: string, ts: string })   — one transcript segment
// Output: postMessage({ module, pronounRatio1P, sentimentScore, coherenceScore,
//                       avgSentenceLength, hedgeRatio })
//         Emitted every EMIT_EVERY_N segments OR every EMIT_EVERY_S seconds,
//         whichever comes first. Minimum 2 segments before first emission.

const WINDOW_SIZE  = 60;   // rolling segment buffer
const EMIT_EVERY_N = 5;    // emit every N segments
const EMIT_EVERY_S = 30;   // or every 30 s if fewer segments have arrived

// ── Word lists ────────────────────────────────────────────────────────────────

const _P1  = new Set(['i', 'me', 'my', 'mine', 'myself']);
const _P_ALL = new Set([
  'i', 'me', 'my', 'mine', 'myself',
  'we', 'us', 'our', 'ours', 'ourselves',
  'you', 'your', 'yours', 'yourself', 'yourselves',
  'he', 'him', 'his', 'himself',
  'she', 'her', 'hers', 'herself',
  'it', 'its', 'itself',
  'they', 'them', 'their', 'theirs', 'themselves',
]);

const _HEDGE = new Set([
  'maybe', 'perhaps', 'might', 'possibly', 'probably', 'sometimes',
  'seem', 'seems', 'seemed', 'apparently', 'supposedly', 'presumably',
  'guess', 'suppose', 'wonder', 'uncertain', 'unsure',
  'somewhat', 'rather', 'fairly', 'quite', 'relatively',
  'generally', 'typically', 'usually', 'often', 'occasionally',
]);

// Compact AFINN-111 subset — highest-magnitude words relevant to telehealth
// Range: -5 (strongly negative) to +5 (strongly positive)
const _AFINN = {
  // Positive
  love:3, happy:3, joy:3, wonderful:3, excellent:3, amazing:4, fantastic:4,
  great:3, good:3, hope:2, hopeful:2, grateful:3, thankful:2, safe:2,
  calm:2, peaceful:3, strong:2, confident:2, positive:2, better:2, fine:2,
  okay:1, nice:2, beautiful:3, bright:2, care:2, trust:2, laugh:2,
  smile:2, enjoy:2, success:3, improve:2, recover:2, healthy:2, relief:2,
  support:2, help:2, free:2, proud:2, excited:2, inspired:2, energetic:2,
  // Negative
  hate:-3, sad:-2, terrible:-3, awful:-3, horrible:-3, pain:-2, hurt:-2,
  fear:-2, afraid:-2, scared:-2, anxious:-2, anxiety:-3, depressed:-3,
  depression:-3, hopeless:-3, worthless:-3, useless:-2, helpless:-3,
  alone:-2, lonely:-3, empty:-2, numb:-2, angry:-2, anger:-2, furious:-3,
  rage:-3, upset:-2, tired:-2, exhausted:-2, sick:-2, fail:-2, failure:-3,
  wrong:-2, bad:-2, worse:-2, worst:-3, nightmare:-3, trauma:-3, abuse:-3,
  shame:-3, guilt:-3, lost:-2, broken:-2, damaged:-2, weak:-1, cry:-2,
  crying:-2, tears:-2, sorry:-1, miss:-1, difficult:-1, hard:-1, struggle:-2,
  die:-3, dead:-3, suicide:-5, kill:-3, destroy:-3, harm:-2, danger:-2,
};

// ── Segment buffer ────────────────────────────────────────────────────────────

const _buf  = [];    // { text: string, words: string[] }
let _segCount  = 0;
let _lastEmitTs = 0;

// ── Tokeniser ─────────────────────────────────────────────────────────────────

function _tokenise(text) {
  return text.toLowerCase().match(/\w+/g) || [];
}

// ── Feature extractors ────────────────────────────────────────────────────────

function _pronounRatio1P(allWords) {
  let p1 = 0, pAll = 0;
  for (const w of allWords) {
    if (_P_ALL.has(w)) pAll++;
    if (_P1.has(w))    p1++;
  }
  return pAll > 0 ? p1 / pAll : 0;
}

function _sentiment(allWords) {
  if (allWords.length === 0) return 0;
  let score = 0;
  for (const w of allWords) score += _AFINN[w] || 0;
  // Divide by word count for per-word average; scale by 0.4 to spread to [-1,+1]
  // (average AFINN hit is ~2–3 so 3 × 0.4 ≈ 1 at saturation)
  return Math.max(-1, Math.min(1, (score / allWords.length) * 0.4));
}

function _avgSentenceLength(segments) {
  const joined = segments.map(s => s.text).join(' ');
  const sentences = joined.split(/[.!?]+/).filter(s => s.trim().length > 0);
  if (sentences.length === 0) return 0;
  const totalWords = sentences.reduce((n, s) => n + (_tokenise(s).length), 0);
  return totalWords / sentences.length;
}

function _hedgeRatio(allWords) {
  if (allWords.length === 0) return 0;
  return allWords.filter(w => _HEDGE.has(w)).length / allWords.length;
}

// TF-IDF cosine coherence: average cosine similarity of adjacent segment pairs.
// Higher score → more topically consistent speech.
function _coherence(segments) {
  if (segments.length < 2) return 1;

  // Build global vocabulary
  const vocabMap = new Map();
  for (const { words } of segments) {
    for (const w of words) {
      if (!vocabMap.has(w)) vocabMap.set(w, vocabMap.size);
    }
  }
  const V = vocabMap.size;
  if (V === 0) return 0;

  const N = segments.length;

  // IDF: smoothed log((N+1)/(df+1)) + 1
  const idf = new Float32Array(V);
  for (const [w, i] of vocabMap) {
    let df = 0;
    for (const seg of segments) {
      for (const sw of seg.words) { if (sw === w) { df++; break; } }
    }
    idf[i] = Math.log((N + 1) / (df + 1)) + 1;
  }

  // Compute TF-IDF vector per segment
  function _vecOf(words) {
    const tf = new Map();
    for (const w of words) tf.set(w, (tf.get(w) || 0) + 1);
    const vec = new Float32Array(V);
    const len = words.length || 1;
    for (const [w, cnt] of tf) {
      const i = vocabMap.get(w);
      if (i !== undefined) vec[i] = (cnt / len) * idf[i];
    }
    return vec;
  }

  const vecs = segments.map(s => _vecOf(s.words));

  // Average cosine similarity of consecutive pairs
  let sum = 0;
  for (let i = 0; i < vecs.length - 1; i++) {
    let dot = 0, magA = 0, magB = 0;
    for (let j = 0; j < V; j++) {
      dot  += vecs[i][j] * vecs[i + 1][j];
      magA += vecs[i][j] * vecs[i][j];
      magB += vecs[i + 1][j] * vecs[i + 1][j];
    }
    sum += (magA > 0 && magB > 0) ? dot / (Math.sqrt(magA) * Math.sqrt(magB)) : 0;
  }
  return sum / (vecs.length - 1);
}

// ── Emit ──────────────────────────────────────────────────────────────────────

function _emit() {
  if (_buf.length < 2) return; // need at least 2 segments for coherence
  const allWords = _buf.flatMap(s => s.words);
  self.postMessage({
    module:           'text.linguistic',
    pronounRatio1P:   +_pronounRatio1P(allWords).toFixed(3),
    sentimentScore:   +_sentiment(allWords).toFixed(3),
    coherenceScore:   +_coherence(_buf).toFixed(3),
    avgSentenceLength: +_avgSentenceLength(_buf).toFixed(1),
    hedgeRatio:       +_hedgeRatio(allWords).toFixed(3),
  });
}

// ── Message handler ───────────────────────────────────────────────────────────

self.onmessage = function(ev) {
  const { text, ts } = ev.data || {};
  if (!text || typeof text !== 'string') return;

  const words = _tokenise(text);
  _buf.push({ text, words });
  if (_buf.length > WINDOW_SIZE) _buf.shift();
  _segCount++;

  const now = Date.now();
  const timeSinceLast = _lastEmitTs > 0 ? now - _lastEmitTs : Infinity;
  const shouldEmit = (_segCount % EMIT_EVERY_N === 0) ||
                     (timeSinceLast >= EMIT_EVERY_S * 1000);
  if (!shouldEmit) return;

  _lastEmitTs = now;
  _emit();
};
