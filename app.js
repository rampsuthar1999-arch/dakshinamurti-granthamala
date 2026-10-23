/* Dakshinamurti Granthamala — static reader (no build step). */
(() => {
'use strict';

const REPO = 'https://github.com/rampsuthar1999-arch/dakshinamurti-granthamala';
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const app = $('#app');
const DEV = '०१२३४५६७८९';
const toDev = n => String(n).replace(/\d/g, d => DEV[d]);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* ---------------- storage (wrapped: may be unavailable) ---------------- */
const store = {
  get(k, d) { try { const v = localStorage.getItem('dg.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('dg.' + k, JSON.stringify(v)); } catch (e) { } },
  raw(k, v) { try { localStorage.setItem('dg.' + k, v); } catch (e) { } },
};

/* ---------------- data ---------------- */
const cache = {};
async function getJSON(url) {
  if (!cache[url]) cache[url] = fetch(url).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .catch(e => { delete cache[url]; throw e; });
  return cache[url];
}
const getLibrary = () => getJSON('data/library.json');
const getBook = id => getJSON(`data/${id}/book.json`);
const getSection = (id, sid) => getJSON(`data/${id}/${sid}.json`);
const getSlokas = id => getJSON(`data/${id}/slokas.json`);

function pageLabel(book, pg) {
  return pg > book.pageOffset ? 'पृ. ' + toDev(pg - book.pageOffset) : 'प्रारम्भिक पृ. ' + toDev(pg);
}
function sectionForPage(book, pg) {
  return book.sections.find(s => pg >= s.start && pg <= s.end);
}
function secLabel(s) { return s.num ? `${toDev(s.num)}. ${s.title}` : s.title; }

/* ---------------- UI helpers ---------------- */
let toastT;
function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('on');
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('on'), 2200);
}
function openLayer(id) { $('#' + id).classList.add('on'); $('#' + id).setAttribute('aria-hidden', 'false'); $('#scrim').classList.add('on'); }
function closeLayers() {
  ['drawer', 'settings'].forEach(id => { $('#' + id).classList.remove('on'); $('#' + id).setAttribute('aria-hidden', 'true'); });
  $('#scrim').classList.remove('on');
}
$('#scrim').onclick = closeLayers;
$$('[data-close]').forEach(b => b.onclick = closeLayers);

function setBar({ title = 'दक्षिणामूर्ति ग्रन्थमाला', back = null, toc = false, split = false } = {}) {
  $('#bar-title').textContent = title;
  const bb = $('#btn-back'); bb.hidden = !back; bb.onclick = () => { location.hash = back; };
  $('#btn-toc').hidden = !toc;
  $('#btn-split').hidden = !split;
  $('#progress').style.width = '0';
  document.title = title === 'दक्षिणामूर्ति ग्रन्थमाला' ? title : `${title} · दक्षिणामूर्ति ग्रन्थमाला`;
}

/* ---------------- settings ---------------- */
let fs = store.get('font', 19);
function applyFont() {
  document.documentElement.style.setProperty('--fs', fs + 'px');
  $('#fs-val').textContent = toDev(fs);
  store.raw('font', String(fs)); offsetsDirty = true;
}
$('#fs-up').onclick = () => { fs = Math.min(30, fs + 1); applyFont(); };
$('#fs-down').onclick = () => { fs = Math.max(14, fs - 1); applyFont(); };
function applyTheme(t) {
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
  $$('[data-theme-set]').forEach(b => b.classList.toggle('on', b.dataset.themeSet === (t || '')));
  const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  $('meta[name=theme-color]').setAttribute('content', bg || '#faf6ee');
}
$$('[data-theme-set]').forEach(b => b.onclick = () => { store.raw('theme', b.dataset.themeSet); applyTheme(b.dataset.themeSet); });
applyTheme(document.documentElement.dataset.theme);
const vo = $('#verses-only');
vo.checked = store.get('versesOnly', false);
document.body.classList.toggle('verses-only', vo.checked);
vo.onchange = () => { document.body.classList.toggle('verses-only', vo.checked); store.set('versesOnly', vo.checked); offsetsDirty = true; };
$('#btn-settings').onclick = () => { applyFont(); openLayer('settings'); };
$('#btn-bookmarks').onclick = () => { location.hash = '#/bookmarks'; };
$('#btn-search').onclick = () => {
  const m = location.hash.match(/^#\/b\/([^/?]+)/);
  location.hash = '#/search' + (m ? '?book=' + m[1] : '');
};
$('#btn-toc').onclick = () => openLayer('drawer');
$('#btn-split').onclick = () => {
  const on = !document.body.classList.contains('split');
  document.body.classList.toggle('split', on); $('#btn-split').classList.toggle('on', on);
  store.set('split', on); offsetsDirty = true;
  if (on) { if (window.innerWidth <= 900) { toast('चौड़ी स्क्रीन पर मूल पृष्ठ साथ में दिखेगा'); } updateSide(true); }
};

/* ---------------- bookmarks ---------------- */
const bms = () => store.get('bm', []);
function bmKey(book, sec, b) { return `${book}/${sec}/${b}`; }
function isMarked(book, sec, b) { return bms().some(x => bmKey(x.book, x.sec, x.b) === bmKey(book, sec, b)); }
function toggleBm(entry) {
  let list = bms(); const k = bmKey(entry.book, entry.sec, entry.b);
  const had = list.some(x => bmKey(x.book, x.sec, x.b) === k);
  list = had ? list.filter(x => bmKey(x.book, x.sec, x.b) !== k) : [{ ...entry, ts: Date.now(), note: '' }, ...list];
  store.set('bm', list); return !had;
}

/* ---------------- Devanagari normalisation for search ---------------- */
const NASAL = 'ङञणनम', CONS = /[क-हक़-य़]/;
const FUZZ = { 'ी': 'ि', 'ू': 'ु', 'ै': 'े', 'ौ': 'ो', 'ई': 'इ', 'ऊ': 'उ', 'ँ': 'ं', 'ॅ': 'े', 'ॉ': 'ो', 'ष': 'श', 'व': 'ब' };
const STRICT = { 'ँ': 'ं' };
const DROP = /[‌‍़॒॑]/;
const PUNCT = /[\s।॥,.;:!?'"“”‘’()\[\]{}\-–—=+*/\\|0-9०-९॰]/;
function normMap(s, fuzzy, wantMap) {
  const tbl = fuzzy ? FUZZ : STRICT; let out = ''; const map = wantMap ? [] : null; let sp = true;
  for (let i = 0; i < s.length; i++) {
    let c = s[i];
    if (DROP.test(c)) continue;
    if (PUNCT.test(c)) { if (!sp) { out += ' '; map && map.push(i); sp = true; } continue; }
    if (NASAL.includes(c) && s[i + 1] === '्' && CONS.test(s[i + 2] || '')) { out += 'ं'; map && map.push(i); i++; sp = false; continue; }
    c = tbl[c] || c;
    out += c; map && map.push(i); sp = false;
  }
  return wantMap ? { n: out, map } : out;
}

/* basic Roman (IAST / Harvard-Kyoto / ITRANS-ish) → Devanagari, for typing without a Hindi keyboard */
const R_V = [['ai', 'ऐ', 'ै'], ['au', 'औ', 'ौ'], ['aa', 'आ', 'ा'], ['ii', 'ई', 'ी'], ['uu', 'ऊ', 'ू'], ['ā', 'आ', 'ा'], ['ī', 'ई', 'ी'], ['ū', 'ऊ', 'ू'],
  ['ṛ', 'ऋ', 'ृ'], ['R', 'ऋ', 'ृ'], ['A', 'आ', 'ा'], ['I', 'ई', 'ी'], ['U', 'ऊ', 'ू'], ['a', 'अ', ''], ['i', 'इ', 'ि'], ['u', 'उ', 'ु'], ['e', 'ए', 'े'], ['o', 'ओ', 'ो']];
const R_C = [['kh', 'ख'], ['gh', 'घ'], ['ch', 'च'], ['Ch', 'छ'], ['chh', 'छ'], ['jh', 'झ'], ['Th', 'ठ'], ['Dh', 'ढ'], ['th', 'थ'], ['dh', 'ध'], ['ph', 'फ'], ['bh', 'भ'],
  ['sh', 'श'], ['Sh', 'ष'], ['ṭh', 'ठ'], ['ḍh', 'ढ'], ['jñ', 'ज्ञ'], ['GY', 'ज्ञ'], ['kṣ', 'क्ष'], ['x', 'क्ष'], ['k', 'क'], ['g', 'ग'], ['c', 'च'], ['j', 'ज'], ['T', 'ट'], ['ṭ', 'ट'],
  ['D', 'ड'], ['ḍ', 'ड'], ['N', 'ण'], ['ṇ', 'ण'], ['t', 'त'], ['d', 'द'], ['n', 'न'], ['p', 'प'], ['f', 'फ'], ['b', 'ब'], ['m', 'म'], ['y', 'य'], ['r', 'र'], ['l', 'ल'],
  ['v', 'व'], ['w', 'व'], ['ś', 'श'], ['z', 'श'], ['ṣ', 'ष'], ['S', 'ष'], ['s', 'स'], ['h', 'ह'], ['ṅ', 'ङ'], ['G', 'ङ'], ['ñ', 'ञ'], ['J', 'ञ']];
function roman2dev(q) {
  if (!/[a-zA-Zāīūṛṃḥṅñṭḍṇśṣ]/.test(q)) return q;
  let out = '', i = 0, prevCons = false;
  const match = (list) => { for (const it of list.slice().sort((a, b) => b[0].length - a[0].length)) if (q.startsWith(it[0], i)) return it; return null; };
  while (i < q.length) {
    const ch = q[i];
    if (ch === 'M' || ch === 'ṃ' || ch === 'ṁ') { if (prevCons) out += ''; out += 'ं'; prevCons = false; i++; continue; }
    if (ch === 'H' || ch === 'ḥ') { out += 'ः'; prevCons = false; i++; continue; }
    const c = match(R_C);
    if (c) { if (prevCons) out += '्'; out += c[1]; prevCons = true; i += c[0].length; continue; }
    const v = match(R_V);
    if (v) { out += prevCons ? v[2] : v[1]; prevCons = false; i += v[0].length; continue; }
    if (prevCons && ch === ' ') out += '';
    out += ch; prevCons = false; i++;
  }
  return out;
}

/* ---------------- router ---------------- */
let cleanup = null;
function parseHash() {
  const h = location.hash.replace(/^#/, '') || '/';
  const [path, qs] = h.split('?');
  return { parts: path.split('/').filter(Boolean).map(decodeURIComponent), q: new URLSearchParams(qs || '') };
}
async function route() {
  closeLayers();
  if (cleanup) { cleanup(); cleanup = null; }
  document.body.classList.remove('split');
  app.onclick = null;
  const { parts, q } = parseHash();
  try {
    if (!parts.length) return await viewLibrary();
    if (parts[0] === 'b' && parts[1]) {
      if (!parts[2]) return await viewBook(parts[1]);
      if (parts[2] === 'r' && parts[3]) return await viewReader(parts[1], parts[3], q);
      if (parts[2] === 'slokas') return await viewSlokas(parts[1]);
      if (parts[2] === 'page' && parts[3]) { await viewBook(parts[1]); return openPage(parts[1], +parts[3]); }
    }
    if (parts[0] === 'search') return await viewSearch(q);
    if (parts[0] === 'bookmarks') return viewBookmarks();
    if (parts[0] === 'about') return viewAbout();
    location.hash = '#/';
  } catch (e) {
    console.error(e);
    app.innerHTML = `<div class="narrow"><p class="empty">सामग्री लोड नहीं हो सकी। कृपया पुनः प्रयास करें।<br><small>${esc(e.message || e)}</small></p></div>`;
  }
}
window.addEventListener('hashchange', route);

/* ---------------- views ---------------- */
const CREDIT = `<div class="credit">
  <strong>आभार —</strong> इस ऐप की समस्त सामग्री <strong>श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी</strong> द्वारा प्रकाशित ग्रन्थों से ली गई है।
  व्याख्या — श्रोत्रिय ब्रह्मनिष्ठ आचार्य महामण्डलेश्वर <strong>श्री १०८ स्वामी महेशानन्द गिरि जी महाराज</strong>।
  समस्त श्रेय एवं अधिकार श्रीदक्षिणामूर्ति मठ के हैं। यह अध्ययन की सुविधा हेतु बनाया गया एक अव्यावसायिक डिजिटल संस्करण है।
  <br><small>पाठ मुद्रित पुस्तक से स्वचालित रूप से (OCR) निकाला गया है, अतः कहीं-कहीं अशुद्धियाँ सम्भव हैं — प्रत्येक पृष्ठ का मूल रूप भी साथ में देखा जा सकता है।</small>
</div>`;

async function viewLibrary() {
  setBar();
  const lib = await getLibrary();
  app.innerHTML = `<div class="wrap">
    <section class="hero">
      <div class="om">ॐ</div>
      <h1>दक्षिणामूर्ति ग्रन्थमाला</h1>
      <p>श्रीदक्षिणामूर्ति मठ प्रकाशन के वेदान्त ग्रन्थ — मूल श्लोक, अर्थ एवं विस्तृत व्याख्या, खोज और मूल पृष्ठों के साथ।</p>
    </section>
    <div class="ornament">✦</div>
    <div class="shelf">
      ${lib.map(b => `<a class="book-card" href="#/b/${b.id}">
        <img src="${b.cover}" alt="${esc(b.title)} मुखपृष्ठ" loading="lazy">
        <div><div class="rom">${esc(b.titleRoman)}</div><h2>${esc(b.title)}</h2>
        <div class="meta">${esc(b.author)}<br>व्याख्या: ${esc(b.commentator)}</div>
        <div class="stats">${toDev(b.slokas)} श्लोक · ${toDev(b.pages)} पृष्ठ</div></div></a>`).join('')}
      <div class="book-card soon"><div class="ph">अ</div><div><div class="rom">Anubhūti Prakāśa</div><h2>अनुभूतिप्रकाश</h2><div class="meta">शीघ्र उपलब्ध</div></div></div>
      <div class="book-card soon"><div class="ph">कृ</div><div><div class="rom">Śrī Kṛṣṇa Sandeśa</div><h2>श्रीकृष्ण-सन्देश</h2><div class="meta">शीघ्र उपलब्ध</div></div></div>
    </div>
    ${CREDIT}
    <p class="footer"><a href="#/about">इस ऐप के बारे में</a> · <a href="${REPO}" target="_blank" rel="noopener">GitHub</a></p>
  </div>`;
  window.scrollTo(0, 0);
}

function fillDrawer(book, curSid) {
  const groups = {};
  book.sections.forEach(s => (groups[s.group] = groups[s.group] || []).push(s));
  $('#drawer-title').textContent = book.title;
  $('#drawer-body').innerHTML =
    `<a href="#/b/${book.id}"><span class="n">⌂</span><span>ग्रन्थ परिचय</span></a>
     <a href="#/b/${book.id}/slokas"><span class="n">श्लो</span><span>श्लोक सूची</span></a>` +
    Object.entries(groups).map(([g, list]) => `<h4>${esc(book.groups[g] || '')}</h4>` +
      list.map(s => `<a href="#/b/${book.id}/r/${s.id}" class="${s.id === curSid ? 'cur' : ''}"><span class="n">${s.num ? toDev(s.num) : '•'}</span><span>${esc(s.title)}</span></a>`).join('')).join('');
  $('#drawer-body').onclick = e => { if (e.target.closest('a')) closeLayers(); };
}

async function viewBook(id) {
  const book = await getBook(id);
  setBar({ title: book.title, back: '#/', toc: true });
  fillDrawer(book);
  const last = store.get('last.' + id, null);
  const lastSec = last && book.sections.find(s => s.id === last.sec);
  const groups = {};
  book.sections.forEach(s => (groups[s.group] = groups[s.group] || []).push(s));
  app.innerHTML = `<div class="narrow">
    <div class="book-head">
      <img src="${book.imgDir}/1.webp" alt="मुखपृष्ठ" data-open-page="1">
      <div>
        <div class="rom" style="color:var(--muted);font-size:13px;letter-spacing:.05em">${esc(book.titleRoman)} · ${esc(book.series)}</div>
        <h1>${esc(book.title)}</h1>
        <p class="by">${esc(book.author)} विरचित<br>व्याख्याता: ${esc(book.commentator)}<br><span style="color:var(--muted)">${esc(book.publisher)}</span></p>
      </div>
    </div>
    <div class="actions">
      ${lastSec ? `<a class="btn primary" href="#/b/${id}/r/${lastSec.id}?b=${last.b}">▶ पढ़ना जारी रखें — ${esc(lastSec.title.replace('ब्रह्मानन्द में ', ''))}</a>`
               : `<a class="btn primary" href="#/b/${id}/r/p1">▶ पढ़ना आरम्भ करें</a>`}
      <a class="btn" href="#/b/${id}/slokas">श्लोक सूची</a>
      <a class="btn" href="#/search?book=${id}">खोजें</a>
    </div>
    <div class="actions" style="margin-top:10px">
      <form id="goto" class="search-input" style="box-shadow:none;padding:2px 4px 2px 12px;border-radius:999px;max-width:340px">
        <input id="goto-n" inputmode="numeric" placeholder="पृष्ठ संख्या (१–${toDev(book.pages - book.pageOffset)})" style="font-size:15px;padding:6px 0" aria-label="पृष्ठ संख्या">
        <button class="btn" type="submit" style="padding:5px 12px">पाठ</button>
        <button class="btn" type="button" id="goto-img" style="padding:5px 12px">मूल</button>
      </form>
    </div>
    ${Object.entries(groups).map(([g, list]) => `<div class="toc-group"><h3>${esc(book.groups[g] || '')}</h3><ul class="toc">` +
      list.map(s => `<li><a href="#/b/${id}/r/${s.id}"><span class="n">${s.num ? toDev(s.num) : '•'}</span><span class="t">${esc(s.title)}</span>
        <span class="s">${s.slokas ? toDev(s.slokas) + ' श्लोक · ' : ''}${pageLabel(book, s.start)}</span></a></li>`).join('') + '</ul></div>').join('')}
    <div class="toc-group"><h3>मूल पृष्ठ</h3><ul class="toc">
      ${book.extraPages.map(p => `<li><a href="#/b/${id}/page/${p.page}"><span class="n">❖</span><span class="t">${esc(p.title)}</span><span class="s">स्कैन</span></a></li>`).join('')}
    </ul></div>
    ${CREDIT}
  </div>`;
  const pnum = () => {
    const v = $('#goto-n').value.trim().replace(/[०-९]/g, d => DEV.indexOf(d));
    const n = parseInt(v, 10); if (!n) return null;
    return Math.min(book.pages, Math.max(1, n + book.pageOffset));
  };
  $('#goto').onsubmit = e => { e.preventDefault(); const pg = pnum(); if (pg) gotoPageText(book, pg); };
  $('#goto-img').onclick = () => { const pg = pnum(); if (pg) openPage(id, pg); };
  app.onclick = e => { const t = e.target.closest('[data-open-page]'); if (t) openPage(id, +t.dataset.openPage); };
  window.scrollTo(0, 0);
}

async function gotoPageText(book, pg) {
  const s = sectionForPage(book, pg);
  if (!s) { openPage(book.id, pg); return; }
  const sec = await getSection(book.id, s.id);
  let bi = sec.blocks.findIndex(b => b[1] >= pg);
  if (bi < 0) bi = 0;
  location.hash = `#/b/${book.id}/r/${s.id}?b=${bi}`;
}

/* ---------- reader ---------- */
let offsetsDirty = true, blockEls = [], blockTops = [], curPg = 0, readerCtx = null;
function computeOffsets() {
  blockTops = blockEls.map(el => el.getBoundingClientRect().top + window.scrollY);
  offsetsDirty = false;
}
function blockAtTop() {
  if (offsetsDirty) computeOffsets();
  const y = window.scrollY + parseInt(getComputedStyle(document.documentElement).getPropertyValue('--bar-h')) + 24;
  let lo = 0, hi = blockTops.length - 1, ans = 0;
  while (lo <= hi) { const m = (lo + hi) >> 1; if (blockTops[m] <= y) { ans = m; lo = m + 1; } else hi = m - 1; }
  return ans;
}
function updateSide(force) {
  if (!readerCtx || !document.body.classList.contains('split')) return;
  const img = $('#side-img'); if (!img) return;
  const pg = curPg;
  if (force || img.dataset.pg !== String(pg)) {
    img.dataset.pg = pg; img.src = `${readerCtx.book.imgDir}/${pg}.webp`;
    $('#side-cap').textContent = pageLabel(readerCtx.book, pg) + ' · मूल पृष्ठ';
  }
}

function renderBlocks(book, sec) {
  let lastPg = 0, html = '';
  const bm = new Set(bms().filter(x => x.book === book.id && x.sec === sec.id).map(x => x.b));
  sec.blocks.forEach((b, i) => {
    const [t, pg, x, n] = b;
    if (pg !== lastPg) {
      html += `<div class="pg" data-pg="${pg}"><button data-open-page="${pg}" title="मूल पृष्ठ देखें">${pageLabel(book, pg)}</button></div>`;
      lastPg = pg;
    }
    const cont = b.includes('c') ? ' c' : '';
    const mk = bm.has(i) ? ' marked' : '';
    if (t === 'v') {
      const main = n ? ' s' : ' q';
      html += `<div class="blk v${main}${mk}" id="b${i}" data-i="${i}" data-pg="${pg}">${n ? `<span class="vnum">प्र. ${toDev(sec.num)} · श्लोक ${toDev(n)}</span>` : ''}${esc(x)}</div>`;
    } else {
      html += `<p class="blk ${t}${cont}${mk}" id="b${i}" data-i="${i}" data-pg="${pg}">${esc(x)}</p>`;
    }
  });
  return html;
}

async function viewReader(id, sid, q) {
  const book = await getBook(id);
  const meta = book.sections.find(s => s.id === sid);
  if (!meta) { location.hash = '#/b/' + id; return; }
  setBar({ title: meta.num ? `${toDev(meta.num)}. ${meta.title.replace('ब्रह्मानन्द में ', '')}` : meta.title, back: '#/b/' + id, toc: true, split: true });
  fillDrawer(book, sid);
  app.innerHTML = `<div class="loading">लोड हो रहा है…</div>`;
  const sec = await getSection(id, sid);
  const idx = book.sections.findIndex(s => s.id === sid);
  const prev = book.sections[idx - 1], next = book.sections[idx + 1];
  const groupName = book.groups[meta.group] || '';
  app.innerHTML = `<div class="reader-shell">
    <article class="reader" id="reader" lang="hi">
      <header class="sec-head">
        <div class="k">${esc(book.title)} · ${esc(groupName)}</div>
        <h1>${meta.num ? `<span style="color:var(--accent)">${toDev(meta.num)}.</span> ` : ''}${esc(meta.title)}</h1>
        <div class="orn">❁</div>
      </header>
      ${renderBlocks(book, sec)}
      <nav class="sec-nav">
        ${prev ? `<a href="#/b/${id}/r/${prev.id}"><small>← पिछला</small>${esc(secLabel(prev))}</a>` : '<span></span>'}
        ${next ? `<a class="next" href="#/b/${id}/r/${next.id}"><small>अगला →</small>${esc(secLabel(next))}</a>` : '<span></span>'}
      </nav>
    </article>
    <aside class="side" id="side"><p class="cap" id="side-cap"></p><img id="side-img" alt="मूल पृष्ठ" data-open-page=""></aside>
  </div>`;
  blockEls = $$('.blk', app);
  offsetsDirty = true;
  readerCtx = { book, sec, meta };
  const split = store.get('split', false);
  document.body.classList.toggle('split', split); $('#btn-split').classList.toggle('on', split);

  // initial position
  let target = null;
  if (q.get('v')) { const vn = +q.get('v'); target = sec.blocks.findIndex(b => b[0] === 'v' && b[3] === vn); }
  else if (q.get('b')) target = +q.get('b');
  else if (q.get('pg')) target = sec.blocks.findIndex(b => b[1] >= +q.get('pg'));
  if (target != null && target >= 0 && $('#b' + target)) {
    const el = $('#b' + target);
    requestAnimationFrame(() => {
      el.scrollIntoView({ block: 'start' });
      if (q.get('hl') !== '0' && (q.get('v') || q.get('q') || q.get('flash'))) { el.classList.add('flash'); }
      if (q.get('q')) highlightIn(el, q.get('q'), q.get('fz') === '1');
    });
  } else window.scrollTo(0, 0);

  // scroll tracking
  let raf = 0;
  const onScroll = () => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const i = blockAtTop();
      const pg = sec.blocks[i] ? sec.blocks[i][1] : meta.start;
      if (pg !== curPg) { curPg = pg; updateSide(); }
      const max = document.documentElement.scrollHeight - window.innerHeight;
      $('#progress').style.width = (max > 0 ? Math.min(100, window.scrollY / max * 100) : 0) + '%';
      store.set('last.' + id, { sec: sid, b: i });
    });
  };
  curPg = sec.blocks[target > 0 ? target : 0]?.[1] || meta.start;
  updateSide(true);
  const onResize = () => { offsetsDirty = true; };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onResize);
  // fonts can shift layout
  document.fonts && document.fonts.ready.then(() => { offsetsDirty = true; });

  // tap a block → tools
  const reader = $('#reader');
  let tools = null;
  const hideTools = () => { if (tools) { tools.remove(); tools = null; } };
  reader.onclick = e => {
    const pgBtn = e.target.closest('[data-open-page]');
    if (pgBtn) { openPage(id, +pgBtn.dataset.openPage); return; }
    if (e.target.closest('.blk-tools')) return;
    const blk = e.target.closest('.blk');
    if (tools) { hideTools(); return; }
    if (!blk || String(getSelection()).trim()) return;
    const i = +blk.dataset.i, b = sec.blocks[i];
    tools = document.createElement('div'); tools.className = 'blk-tools';
    const marked = isMarked(id, sid, i);
    const link = `${location.origin}${location.pathname}#/b/${id}/r/${sid}?${b[0] === 'v' && b[3] ? 'v=' + b[3] : 'b=' + i + '&flash=1'}`;
    tools.innerHTML = `
      <button data-a="bm"><svg viewBox="0 0 24 24"><path d="M7 4h10v16l-5-3.5L7 20z" ${marked ? 'fill="currentColor"' : ''}/></svg>${marked ? 'हटाएँ' : 'बुकमार्क'}</button>
      <button data-a="copy"><svg viewBox="0 0 24 24"><rect x="8" y="8" width="11" height="12" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h9"/></svg>कॉपी</button>
      <button data-a="share"><svg viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1 1M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1-1"/></svg>लिंक</button>
      <button data-a="page"><svg viewBox="0 0 24 24"><rect x="5" y="3.5" width="14" height="17" rx="1.5"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/></svg>मूल</button>
      <button data-a="err"><svg viewBox="0 0 24 24"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/></svg>त्रुटि</button>`;
    reader.appendChild(tools);
    const r = blk.getBoundingClientRect(), rr = reader.getBoundingClientRect();
    let top = r.top - rr.top - tools.offsetHeight - 6;
    if (r.top - tools.offsetHeight < 70) top = r.top - rr.top + Math.min(r.height, 60) + 6;
    tools.style.top = top + 'px';
    tools.style.left = Math.max(0, Math.min(rr.width - tools.offsetWidth, (e.clientX - rr.left) - tools.offsetWidth / 2)) + 'px';
    tools.onclick = async ev => {
      const a = ev.target.closest('button')?.dataset.a; if (!a) return;
      const where = `${book.title} · ${secLabel(meta)}${b[0] === 'v' && b[3] ? ' · श्लोक ' + toDev(b[3]) : ''} · ${pageLabel(book, b[1])}`;
      if (a === 'bm') {
        const on = toggleBm({ book: id, sec: sid, b: i, pg: b[1], text: b[2].slice(0, 220), where });
        blk.classList.toggle('marked', on); toast(on ? 'बुकमार्क जोड़ा गया' : 'बुकमार्क हटाया गया');
      } else if (a === 'copy') {
        try { await navigator.clipboard.writeText(`${b[2]}\n— ${where}`); toast('कॉपी हो गया'); } catch (er) { toast('कॉपी नहीं हो सका'); }
      } else if (a === 'share') {
        if (navigator.share) { try { await navigator.share({ title: where, url: link }); } catch (er) { } }
        else { try { await navigator.clipboard.writeText(link); toast('लिंक कॉपी हो गया'); } catch (er) { toast(link); } }
      } else if (a === 'page') {
        openPage(id, b[1]);
      } else if (a === 'err') {
        const title = `पाठ-त्रुटि: ${book.titleRoman} ${meta.num ? 'प्र. ' + meta.num : meta.title}, ${pageLabel(book, b[1])}`;
        const body = `**स्थान:** ${where}\n**लिंक:** ${link}\n\n**वर्तमान पाठ:**\n> ${b[2].slice(0, 600).replace(/\n/g, '\n> ')}\n\n**सही पाठ / टिप्पणी:**\n\n`;
        window.open(`${REPO}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`, '_blank', 'noopener');
      }
      hideTools();
    };
  };
  const side = $('#side');
  side.onclick = () => openPage(id, curPg);
  cleanup = () => {
    window.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onResize);
    readerCtx = null; blockEls = []; hideTools();
  };
}

function highlightIn(el, query, fuzzy) {
  const words = normMap(roman2dev(query), fuzzy).trim().split(' ').filter(Boolean);
  if (!words.length) return;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  const nodes = []; while (walker.nextNode()) if (!walker.currentNode.parentElement.closest('.vnum')) nodes.push(walker.currentNode);
  nodes.forEach(node => {
    const s = node.nodeValue, { n, map } = normMap(s, fuzzy, true);
    const ranges = [];
    words.forEach(w => { let k = n.indexOf(w); while (k >= 0) { ranges.push([map[k], map[k + w.length - 1] + 1]); k = n.indexOf(w, k + w.length); } });
    if (!ranges.length) return;
    ranges.sort((a, b) => a[0] - b[0]);
    const frag = document.createDocumentFragment(); let pos = 0;
    ranges.forEach(([a, b]) => {
      if (a < pos) return;
      b = extendCluster(s, b);
      frag.append(s.slice(pos, a)); const m = document.createElement('mark'); m.textContent = s.slice(a, b); frag.append(m); pos = b;
    });
    frag.append(s.slice(pos)); node.replaceWith(frag);
  });
}
// extend highlight to the end of the grapheme cluster (matras, virama, nukta)
function extendCluster(s, b) { while (b < s.length && /[ऀ-ःऺ-ॏॕ-ॗॢॣ‌‍]/.test(s[b])) b++; return b; }

/* ---------- original page viewer ---------- */
let pvCtx = null;
async function openPage(id, pg) {
  const book = await getBook(id);
  pg = Math.max(1, Math.min(book.pages, pg));
  pvCtx = { book, pg };
  const pv = $('#pageview');
  pv.classList.add('on'); pv.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  const img = $('#pv-img');
  img.src = `${book.imgDir}/${pg}.webp`;
  img.alt = `मूल पृष्ठ — ${pageLabel(book, pg)}`;
  $('#pv-label').textContent = `${pageLabel(book, pg)} / ${toDev(book.pages - book.pageOffset)}`;
  $('#pv-prev').disabled = pg <= 1; $('#pv-next').disabled = pg >= book.pages;
  $('#pv-totext').hidden = !sectionForPage(book, pg);
  $('#pv-scroll').scrollTop = 0; img.classList.remove('zoom');
  if (pg < book.pages) { const pre = new Image(); pre.src = `${book.imgDir}/${pg + 1}.webp`; }
}
function closePage() {
  const pv = $('#pageview'); pv.classList.remove('on'); pv.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  if (/^#\/b\/[^/]+\/page\//.test(location.hash)) history.replaceState(null, '', location.hash.replace(/\/page\/\d+.*/, ''));
  pvCtx = null;
}
$('#pv-close').onclick = closePage;
$('#pv-img').onclick = e => e.target.classList.toggle('zoom');
$('#pv-prev').onclick = () => pvCtx && openPage(pvCtx.book.id, pvCtx.pg - 1);
$('#pv-next').onclick = () => pvCtx && openPage(pvCtx.book.id, pvCtx.pg + 1);
$('#pv-totext').onclick = () => { if (!pvCtx) return; const { book, pg } = pvCtx; closePage(); gotoPageText(book, pg); };
(() => { // swipe between pages
  let sx = 0, sy = 0;
  $('#pv-scroll').addEventListener('touchstart', e => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
  $('#pv-scroll').addEventListener('touchend', e => {
    if (!pvCtx || e.changedTouches.length !== 1 || (window.visualViewport && visualViewport.scale > 1.05)) return;
    const dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy) * 1.5) openPage(pvCtx.book.id, pvCtx.pg + (dx < 0 ? 1 : -1));
  }, { passive: true });
})();

document.addEventListener('keydown', e => {
  if (pvCtx) {
    if (e.key === 'Escape') closePage();
    else if (e.key === 'ArrowRight') $('#pv-next').click();
    else if (e.key === 'ArrowLeft') $('#pv-prev').click();
    return;
  }
  if (e.key === 'Escape') closeLayers();
  if (e.key === '/' && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); $('#btn-search').click(); }
});

/* ---------- śloka index ---------- */
async function viewSlokas(id) {
  const book = await getBook(id);
  setBar({ title: book.title + ' · श्लोक सूची', back: '#/b/' + id, toc: true });
  fillDrawer(book);
  const sl = await getSlokas(id);
  const bySec = {};
  sl.forEach(r => (bySec[r[0]] = bySec[r[0]] || []).push(r));
  app.innerHTML = `<div class="narrow">
    <div class="search-box"><div class="search-input">
      <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>
      <input id="sl-f" placeholder="श्लोक का आरम्भ लिखें, या ६.१२ जैसा संदर्भ" autocomplete="off" aria-label="श्लोक खोजें">
    </div></div>
    <div id="sl-body"></div></div>`;
  const render = (f) => {
    const ref = f.replace(/[०-९]/g, d => DEV.indexOf(d)).match(/^\s*(\d+)\s*[.:,\s]\s*(\d+)\s*$/);
    const nf = normMap(roman2dev(f), true).trim();
    let html = '';
    book.sections.filter(s => s.num).forEach(s => {
      let rows = bySec[s.num] || [];
      if (ref) rows = rows.filter(r => r[0] === +ref[1] && r[1] === +ref[2]);
      else if (nf) rows = rows.filter(r => normMap(r[4], true).includes(nf));
      if (!rows.length) return;
      html += `<h3 class="sl-sec">${toDev(s.num)}. ${esc(s.title)}</h3><ul class="sl-list">` +
        rows.map(r => `<li><a href="#/b/${id}/r/${s.id}?v=${r[1]}"><span class="ref">${toDev(r[0])}.${toDev(r[1])}</span><span class="ln">${esc(r[4])}</span><span class="pgn">${pageLabel(book, r[3])}</span></a></li>`).join('') + '</ul>';
    });
    $('#sl-body').innerHTML = html || '<p class="empty">कोई श्लोक नहीं मिला</p>';
  };
  render('');
  let t; $('#sl-f').oninput = e => { clearTimeout(t); t = setTimeout(() => render(e.target.value), 120); };
  window.scrollTo(0, 0);
}

/* ---------- search ---------- */
const searchIndex = {};
async function loadIndex(id) {
  if (searchIndex[id]) return searchIndex[id];
  const book = await getBook(id);
  const secs = await Promise.all(book.sections.map(s => getSection(id, s.id)));
  const items = [];
  secs.forEach((sec, si) => sec.blocks.forEach((b, i) => {
    if (b[0] === 'h') return;
    items.push({ si, i, t: b[0], pg: b[1], x: b[2], n: b[3], f: normMap(b[2], true), s: normMap(b[2], false) });
  }));
  return (searchIndex[id] = { book, items });
}
async function viewSearch(q) {
  const lib = await getLibrary();
  const id = q.get('book') || lib[0].id;
  const book = await getBook(id);
  setBar({ title: 'खोजें · ' + book.title, back: '#/b/' + id, toc: true });
  fillDrawer(book);
  const st = { q: q.get('q') || '', mode: q.get('m') || 'all', fz: q.get('fz') !== '0' };
  app.innerHTML = `<div class="narrow">
    <div class="search-box">
      <form class="search-input" id="sf">
        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>
        <input id="sq" type="search" placeholder="शब्द खोजें — जैसे ब्रह्मानन्द, कूटस्थ" value="${esc(st.q)}" autocomplete="off" aria-label="खोज">
      </form>
      <div class="filters">
        <button class="chip" data-m="all">सब</button>
        <button class="chip" data-m="v">केवल श्लोक</button>
        <button class="chip" data-m="p">केवल व्याख्या</button>
        <button class="chip" data-fz>सरल मिलान</button>
      </div>
    </div>
    <div id="sr"><p class="hint">पूरे ग्रन्थ (${toDev(book.pages)} पृष्ठ) में खोजें। हिन्दी/संस्कृत में लिखें, या रोमन में भी — जैसे <kbd>kutastha</kbd>, <kbd>brahmAnanda</kbd>।<br>
    “सरल मिलान” चालू होने पर ह्रस्व-दीर्घ मात्रा (ि/ी, ु/ू), े/ै, ँ/ं, श/ष तथा ब/व का भेद अनदेखा किया जाता है — जिससे OCR की छोटी त्रुटियों के बावजूद परिणाम मिलें।</p></div>
  </div>`;
  const input = $('#sq');
  const syncChips = () => {
    $$('[data-m]').forEach(c => c.classList.toggle('on', c.dataset.m === st.mode));
    $('[data-fz]').classList.toggle('on', st.fz);
  };
  syncChips();
  let limit = 60;
  const run = async () => {
    const qq = st.q.trim();
    history.replaceState(null, '', `#/search?book=${id}${qq ? '&q=' + encodeURIComponent(qq) : ''}${st.mode !== 'all' ? '&m=' + st.mode : ''}${st.fz ? '' : '&fz=0'}`);
    if (!qq) return;
    const sr = $('#sr');
    if (!searchIndex[id]) sr.innerHTML = '<p class="loading">खोज-सूची तैयार हो रही है…</p>';
    const { items } = await loadIndex(id);
    const dq = roman2dev(qq);
    const words = normMap(dq, st.fz).trim().split(' ').filter(Boolean);
    if (!words.length) return;
    const key = st.fz ? 'f' : 's';
    const res = items.filter(it => (st.mode === 'all' || (st.mode === 'v' ? it.t === 'v' : it.t !== 'v')) && words.every(w => it[key].includes(w)));
    const counts = {}; res.forEach(r => counts[r.si] = (counts[r.si] || 0) + 1);
    const sec = book.sections;
    sr.innerHTML = `<p class="res-meta">${dq !== qq ? `“${esc(dq)}” — ` : ''}${toDev(res.length)} परिणाम${res.length ? ' · ' + Object.entries(counts).map(([si, c]) => `${sec[si].num ? 'प्र. ' + toDev(sec[si].num) : sec[si].title}: ${toDev(c)}`).join(', ') : ''}</p>` +
      res.slice(0, limit).map(it => {
        const s = sec[it.si];
        const snip = snippet(it.x, words, st.fz);
        return `<a class="res ${it.t === 'v' ? 'v' : ''}" href="#/b/${id}/r/${s.id}?b=${it.i}&q=${encodeURIComponent(qq)}${st.fz ? '&fz=1' : ''}">
          <div class="where">${s.num ? 'प्र. ' + toDev(s.num) + ' · ' : ''}${esc(s.title)}${it.t === 'v' && it.n ? ' · श्लोक ' + toDev(it.n) : ''} · ${pageLabel(book, it.pg)}</div>
          <div class="snip">${snip}</div></a>`;
      }).join('') +
      (res.length > limit ? `<p style="text-align:center"><button class="btn" id="more">और दिखाएँ (${toDev(res.length - limit)})</button></p>` : '') +
      (!res.length ? `<p class="empty">कोई परिणाम नहीं मिला${st.fz ? '' : ' — “सरल मिलान” चालू करके देखें'}।</p>` : '');
    const more = $('#more'); if (more) more.onclick = () => { limit += 100; run(); };
  };
  let t;
  input.oninput = () => { st.q = input.value; limit = 60; clearTimeout(t); t = setTimeout(run, 250); };
  $('#sf').onsubmit = e => { e.preventDefault(); st.q = input.value; run(); input.blur(); };
  $$('[data-m]').forEach(c => c.onclick = () => { st.mode = c.dataset.m; syncChips(); limit = 60; run(); });
  $('[data-fz]').onclick = () => { st.fz = !st.fz; syncChips(); limit = 60; run(); };
  if (st.q) run(); else setTimeout(() => input.focus(), 50);
  window.scrollTo(0, 0);
}
function snippet(x, words, fuzzy) {
  const { n, map } = normMap(x, fuzzy, true);
  const ranges = [];
  words.forEach(w => { let k = n.indexOf(w); while (k >= 0) { ranges.push([map[k], extendCluster(x, map[k + w.length - 1] + 1)]); k = n.indexOf(w, k + w.length); } });
  ranges.sort((a, b) => a[0] - b[0]);
  const first = ranges.length ? ranges[0][0] : 0;
  let a = Math.max(0, first - 90), b = Math.min(x.length, first + 210);
  if (a > 0) { const sp = x.indexOf(' ', a); if (sp > 0 && sp < first) a = sp + 1; }
  let out = '', pos = a;
  ranges.forEach(([s, e]) => { if (s < pos || e > b) return; out += esc(x.slice(pos, s)) + '<mark>' + esc(x.slice(s, e)) + '</mark>'; pos = e; });
  out += esc(x.slice(pos, b));
  return (a > 0 ? '… ' : '') + out.replace(/\n/g, ' / ') + (b < x.length ? ' …' : '');
}

/* ---------- bookmarks ---------- */
function viewBookmarks() {
  setBar({ title: 'बुकमार्क', back: '#/' });
  const list = bms();
  app.innerHTML = `<div class="narrow"><h1 style="font-family:var(--body);margin:18px 0 14px">बुकमार्क एवं टिप्पणियाँ</h1>
    ${list.length ? list.map((b, k) => `<div class="bm" data-k="${k}">
      <div class="where">${esc(b.where)}</div>
      <div class="snip">${esc(b.text.replace(/\n/g, ' / '))}${b.text.length >= 220 ? '…' : ''}</div>
      ${b.note ? `<div class="note">${esc(b.note)}</div>` : ''}
      <div class="row"><a href="#/b/${b.book}/r/${b.sec}?b=${b.b}&flash=1">पढ़ें →</a>
        <button data-a="note">${b.note ? 'टिप्पणी बदलें' : 'टिप्पणी जोड़ें'}</button><button data-a="del">हटाएँ</button></div>
    </div>`).join('') : '<p class="empty">अभी कोई बुकमार्क नहीं है।<br>पढ़ते समय किसी अनुच्छेद या श्लोक पर टैप करें और “बुकमार्क” चुनें।</p>'}
    <p class="hint" style="margin-top:24px">बुकमार्क इसी डिवाइस/ब्राउज़र में सुरक्षित रहते हैं।</p></div>`;
  app.onclick = e => {
    const btn = e.target.closest('button[data-a]'); if (!btn) return;
    const card = btn.closest('.bm'), k = +card.dataset.k, l = bms();
    if (btn.dataset.a === 'del') { l.splice(k, 1); store.set('bm', l); viewBookmarks(); }
    if (btn.dataset.a === 'note') {
      if (card.querySelector('textarea')) return;
      const ta = document.createElement('textarea');
      ta.value = l[k].note || ''; ta.rows = 3;
      ta.style.cssText = 'width:100%;margin-top:8px;font:15px var(--body);padding:8px;border-radius:8px;border:1px solid var(--rule);background:var(--bg);color:var(--ink)';
      const save = document.createElement('button'); save.textContent = 'सहेजें'; save.className = 'btn'; save.style.marginTop = '6px';
      save.onclick = () => { const l2 = bms(); l2[k].note = ta.value.trim(); store.set('bm', l2); viewBookmarks(); };
      card.append(ta, save); ta.focus();
    }
  };
  window.scrollTo(0, 0);
}

/* ---------- about ---------- */
function viewAbout() {
  setBar({ title: 'परिचय', back: '#/' });
  app.innerHTML = `<div class="narrow about">
    <h1 style="font-family:var(--body);margin-top:18px">इस ऐप के बारे में</h1>
    <p>दक्षिणामूर्ति ग्रन्थमाला, श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी के ग्रन्थों को मोबाइल और कम्प्यूटर पर सुविधा से पढ़ने, खोजने और अध्ययन करने के लिये बनाया गया एक निःशुल्क डिजिटल पाठ है।</p>
    ${CREDIT}
    <h2>सुविधाएँ</h2>
    <ul>
      <li>प्रकरण-वार पाठ — मूल श्लोक, अर्थ एवं व्याख्या अलग-अलग शैली में</li>
      <li>प्रत्येक पृष्ठ का मूल स्कैन — पाठ के साथ-साथ (चौड़ी स्क्रीन पर) या अलग से</li>
      <li>पूरे ग्रन्थ में खोज (देवनागरी या रोमन में), OCR-त्रुटियों को सहने वाला “सरल मिलान”</li>
      <li>श्लोक सूची — आरम्भिक शब्द या संदर्भ (जैसे ६.१२) से श्लोक पर पहुँचें</li>
      <li>बुकमार्क, टिप्पणियाँ, अन्तिम पढ़ा स्थान, अक्षर आकार और रंग-योजना</li>
    </ul>
    <h2>पाठ की शुद्धता</h2>
    <p>पाठ मुद्रित पुस्तक के स्कैन से स्वचालित रूप से निकाला गया है। संस्कृत श्लोकों तथा कुछ मात्राओं (जैसे है/हे, ं/ँ) में त्रुटियाँ हो सकती हैं। किसी भी अंश पर टैप करके “त्रुटि” चुनें — इससे सुधार हेतु सूचना भेजी जा सकती है।</p>
    <p class="footer"><a href="${REPO}" target="_blank" rel="noopener">GitHub पर स्रोत</a></p>
  </div>`;
  window.scrollTo(0, 0);
}

route();
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
})();
