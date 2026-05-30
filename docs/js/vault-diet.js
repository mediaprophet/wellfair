'use strict';

// ── Diet Log — Sprint 6 ───────────────────────────────────────────────────────
// Depends on: vault-idb.js (_dbPut, _dbGet, _dbGetAll, _dbDelete, _ST_DIET_LOG)
//
// Record shape (wf-dl):
//   id         string   'dl-<timestamp>'
//   date       string   'YYYY-MM-DD'
//   time       string   'HH:MM'
//   meal       string   'breakfast'|'lunch'|'dinner'|'snack'|'drink'
//   name       string   food name (required)
//   brand      string   brand / product name (optional)
//   quantity   number   amount consumed
//   unit       string   'g'|'ml'|'serving'|'piece'|'cup'|'tbsp'|'tsp'
//   kcal       number   energy in kcal
//   protein_g  number   protein g
//   carbs_g    number   carbohydrate g
//   fat_g      number   fat g
//   fiber_g    number|null
//   sugar_g    number|null
//   sodium_mg  number|null   sodium in mg
//   notes      string
//   created_at string   ISO timestamp
//
// Nutrient schema aligns with Open Food Facts / USDA FoodData Central field names.

// ── Public API ────────────────────────────────────────────────────────────────

async function dlAddEntry(fields) {
  if (!fields.name || !fields.name.trim()) throw new Error('Food name is required.');
  const record = {
    id:         'dl-' + Date.now(),
    date:       fields.date       || _todayStr(),
    time:       fields.time       || _nowTime(),
    meal:       fields.meal       || 'snack',
    name:       fields.name.trim(),
    brand:      (fields.brand || '').trim(),
    quantity:   _num(fields.quantity, 1),
    unit:       fields.unit       || 'serving',
    kcal:       _num(fields.kcal,      0),
    protein_g:  _num(fields.protein_g, 0),
    carbs_g:    _num(fields.carbs_g,   0),
    fat_g:      _num(fields.fat_g,     0),
    fiber_g:    fields.fiber_g   != null ? _num(fields.fiber_g,  0) : null,
    sugar_g:    fields.sugar_g   != null ? _num(fields.sugar_g,  0) : null,
    sodium_mg:  fields.sodium_mg != null ? _num(fields.sodium_mg,0) : null,
    notes:      (fields.notes || '').trim(),
    created_at: new Date().toISOString(),
  };
  await _dbPut(_ST_DIET_LOG, record);
  return record;
}

async function dlGetEntry(id) {
  return _dbGet(_ST_DIET_LOG, id);
}

async function dlGetByDate(dateStr) {
  const all = await _dbGetAll(_ST_DIET_LOG);
  return all.filter(r => r.date === dateStr)
            .sort((a, b) => a.time.localeCompare(b.time));
}

async function dlDeleteEntry(id) {
  return _dbDelete(_ST_DIET_LOG, id);
}

// Returns aggregate nutrient totals for an array of entries.
function dlDailyTotals(entries) {
  const t = { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };
  for (const e of entries) {
    t.kcal      += e.kcal      || 0;
    t.protein_g += e.protein_g || 0;
    t.carbs_g   += e.carbs_g   || 0;
    t.fat_g     += e.fat_g     || 0;
  }
  t.kcal      = Math.round(t.kcal);
  t.protein_g = +t.protein_g.toFixed(1);
  t.carbs_g   = +t.carbs_g.toFixed(1);
  t.fat_g     = +t.fat_g.toFixed(1);
  return t;
}

// ── Internal helpers ──────────────────────────────────────────────────────────

function _num(val, fallback) {
  const n = parseFloat(val);
  return isNaN(n) ? fallback : n;
}

function _todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function _nowTime() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}
