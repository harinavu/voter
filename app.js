/**
 * Sakhavaram Voter Search — app.js
 * Loads voters.json, provides instant search, filtering, pagination and modal.
 */

'use strict';

// ========== CONFIG ==========
const PAGE_SIZE = 24; // voters per page

// ========== STATE ==========
let allVoters   = [];    // full dataset
let filtered    = [];    // after search+filter
let currentPage = 1;
let activeFilter = 'all';
let currentVoter = null; // for modal

// ========== DOM REFS ==========
const searchInput      = document.getElementById('searchInput');
const searchBtn        = document.getElementById('searchBtn');
const clearBtn         = document.getElementById('clearBtn');
const filterChips      = document.querySelectorAll('.filter-chip');
const ageMinInput      = document.getElementById('ageMin');
const ageMaxInput      = document.getElementById('ageMax');
const resultsBar       = document.getElementById('resultsBar');
const resultsCount     = document.getElementById('resultsCount');
const exportBtn        = document.getElementById('exportBtn');
const voterGrid        = document.getElementById('voterGrid');
const paginationEl     = document.getElementById('pagination');
const stateWelcome     = document.getElementById('stateWelcome');
const stateLoading     = document.getElementById('stateLoading');
const stateEmpty       = document.getElementById('stateEmpty');
const totalVotersCount = document.getElementById('totalVotersCount');

// Modal
const modalOverlay    = document.getElementById('modalOverlay');
const modalClose      = document.getElementById('modalClose');
const modalAvatar     = document.getElementById('modalAvatar');
const modalName       = document.getElementById('modalName');
const modalId         = document.getElementById('modalId');
const dVoterId        = document.getElementById('dVoterId');
const dSerial         = document.getElementById('dSerial');
const dAge            = document.getElementById('dAge');
const dGender         = document.getElementById('dGender');
const dRelationType   = document.getElementById('dRelationType');
const dRelationName   = document.getElementById('dRelationName');
const dHouse          = document.getElementById('dHouse');
const dPartSerial     = document.getElementById('dPartSerial');

// ========== LOAD DATA ==========
async function loadVoters() {
  try {
    const res = await fetch('voters.json');
    if (!res.ok) throw new Error('Failed to load voters.json');
    allVoters = await res.json();
    totalVotersCount.textContent = allVoters.length.toLocaleString('en-IN');
    console.log(`Loaded ${allVoters.length} voters`);
  } catch (err) {
    console.error('Error loading voter data:', err);
    totalVotersCount.textContent = 'N/A';
    stateWelcome.querySelector('.state-desc').textContent =
      'Could not load voter data. Make sure voters.json is in the same folder.';
  }
}

// ========== SEARCH & FILTER ==========
function normalizeText(str) {
  return (str || '').toLowerCase().trim();
}

function runSearch() {
  const query = normalizeText(searchInput.value);
  const ageMin = parseInt(ageMinInput.value) || 0;
  const ageMax = parseInt(ageMaxInput.value) || 999;

  if (!query && activeFilter === 'all' && !ageMinInput.value && !ageMaxInput.value) {
    showState('welcome');
    resultsBar.style.display = 'none';
    voterGrid.innerHTML = '';
    paginationEl.innerHTML = '';
    return;
  }

  showState('loading');

  // Slight debounce for large data
  setTimeout(() => {
    filtered = allVoters.filter(v => {
      // Gender filter
      if (activeFilter === 'male' && v.gender !== 'Male') return false;
      if (activeFilter === 'female' && v.gender === 'Male') return false;

      // Age filter
      const age = parseInt(v.age) || 0;
      if (age < ageMin || age > ageMax) return false;

      // Text search
      if (query) {
        const fields = [
          v.voter_name, v.voter_id, v.relation_name,
          v.house_number, v.full_serial, v.part_serial
        ].map(normalizeText).join(' ');
        if (!fields.includes(query)) return false;
      }

      return true;
    });

    currentPage = 1;
    renderResults(query);
  }, 50);
}

// ========== RENDER RESULTS ==========
function renderResults(query = '') {
  if (filtered.length === 0) {
    showState('empty');
    resultsBar.style.display = 'none';
    voterGrid.innerHTML = '';
    paginationEl.innerHTML = '';
    return;
  }

  showState('results');

  // Update results bar
  resultsBar.style.display = 'flex';
  resultsCount.innerHTML = `Showing <strong>${filtered.length.toLocaleString('en-IN')}</strong> voter${filtered.length !== 1 ? 's' : ''}`;

  // Paginate
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageVoters = filtered.slice(start, start + PAGE_SIZE);

  voterGrid.innerHTML = pageVoters.map((v, i) => renderVoterCard(v, start + i, query)).join('');

  // Attach click handlers
  voterGrid.querySelectorAll('.voter-card').forEach((card, i) => {
    card.addEventListener('click', () => openModal(pageVoters[i]));
    card.addEventListener('keydown', e => { if (e.key === 'Enter') openModal(pageVoters[i]); });
  });

  renderPagination(totalPages);
}

function getInitial(name) {
  if (!name) return '?';
  // Get first actual character (skip spaces / special)
  const match = name.match(/[\u0C00-\u0C7F\w]/u);
  return match ? match[0] : name[0] || '?';
}

function getAvatarClass(gender) {
  if (gender === 'Male') return 'avatar-male';
  if (gender === 'Female') return 'avatar-female';
  return 'avatar-other';
}
function getAvatarEmoji(gender) {
  if (gender === 'Male') return '👨';
  if (gender === 'Female') return '👩';
  return '🧑';
}
function getGenderBadgeClass(gender) {
  if (gender === 'Male') return 'gender-male';
  if (gender === 'Female') return 'gender-female';
  return '';
}

function highlight(text, query) {
  if (!query || !text) return escapeHtml(text || '—');
  const escaped = escapeHtml(text);
  const escapedQuery = escapeHtml(query).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return escaped.replace(new RegExp(`(${escapedQuery})`, 'gi'), '<mark>$1</mark>');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderVoterCard(v, idx, query) {
  const avatarClass = getAvatarClass(v.gender);
  const avatarEmoji = getAvatarEmoji(v.gender);
  const genderBadge = v.gender
    ? `<span class="gender-badge ${getGenderBadgeClass(v.gender)}">${v.gender}</span>`
    : '';
  const relBadge = v.relation_type
    ? `<span class="relation-badge">${v.relation_type}</span>` : '';
  const relName = v.relation_name ? highlight(v.relation_name, query) : '—';

  return `
    <div class="voter-card" role="button" tabindex="0" aria-label="View details for ${escapeHtml(v.voter_name)}">
      <div class="voter-card-top">
        <div class="voter-avatar ${avatarClass}">${avatarEmoji}</div>
        <div class="voter-card-name-wrap">
          <div class="voter-card-name">${highlight(v.voter_name, query) || '—'}</div>
          <span class="voter-card-id">${highlight(v.voter_id, query) || '—'}</span>
        </div>
      </div>
      <div class="voter-card-details">
        <div class="voter-card-detail">
          <span class="detail-key">Age</span>
          <span class="detail-val">${v.age || '—'}</span>
        </div>
        <div class="voter-card-detail">
          <span class="detail-key">Gender</span>
          <span class="detail-val">${genderBadge || '—'}</span>
        </div>
        <div class="voter-card-detail">
          <span class="detail-key">House No.</span>
          <span class="detail-val">${highlight(v.house_number, query) || '—'}</span>
        </div>
        <div class="voter-card-detail">
          <span class="detail-key">Serial</span>
          <span class="detail-val">${escapeHtml(v.full_serial) || '—'}</span>
        </div>
        <div class="voter-card-relation">
          ${relBadge}
          <span class="relation-name">${relName}</span>
        </div>
      </div>
    </div>
  `;
}

// ========== PAGINATION ==========
function renderPagination(totalPages) {
  if (totalPages <= 1) { paginationEl.innerHTML = ''; return; }

  let html = '';

  // Prev button
  html += `<button class="page-btn" id="pagePrev" onclick="goPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>‹ Prev</button>`;

  // Page numbers with ellipsis
  const pages = getPageNumbers(currentPage, totalPages);
  pages.forEach(p => {
    if (p === '...') {
      html += `<span class="page-btn" style="cursor:default;opacity:0.4">…</span>`;
    } else {
      html += `<button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="goPage(${p})">${p}</button>`;
    }
  });

  // Next button
  html += `<button class="page-btn" id="pageNext" onclick="goPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next ›</button>`;

  paginationEl.innerHTML = html;
}

function getPageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [];
  if (current <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total);
  } else if (current >= total - 3) {
    pages.push(1, '...', total-4, total-3, total-2, total-1, total);
  } else {
    pages.push(1, '...', current-1, current, current+1, '...', total);
  }
  return pages;
}

window.goPage = function(page) {
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  renderResults(normalizeText(searchInput.value));
  window.scrollTo({ top: 400, behavior: 'smooth' });
};

// ========== MODAL ==========
function openModal(voter) {
  currentVoter = voter;

  const avatarClass = getAvatarClass(voter.gender);
  const avatarEmoji = getAvatarEmoji(voter.gender);

  modalAvatar.textContent = avatarEmoji;
  modalAvatar.className = `modal-avatar ${avatarClass}`;
  modalName.textContent = voter.voter_name || '—';
  modalId.textContent = voter.voter_id || '—';

  dVoterId.textContent = voter.voter_id || '—';
  dSerial.textContent = voter.full_serial || '—';
  dAge.textContent = voter.age ? `${voter.age} years` : '—';
  dGender.textContent = voter.gender || '—';
  dRelationType.textContent = voter.relation_type || '—';
  dRelationName.textContent = voter.relation_name || '—';
  dHouse.textContent = voter.house_number || '—';
  dPartSerial.textContent = voter.part_serial ? `Part ${voter.part_serial}` : '—';

  modalOverlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  modalClose.focus();
}

function closeModal() {
  modalOverlay.style.display = 'none';
  document.body.style.overflow = '';
  currentVoter = null;
}

window.printVoter = function() {
  if (!currentVoter) return;
  const v = currentVoter;
  const printWin = window.open('', '_blank', 'width=600,height=700');
  printWin.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Voter Details — ${v.voter_id}</title>
      <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Telugu:wght@400;600&family=Inter:wght@400;600&display=swap" rel="stylesheet">
      <style>
        body { font-family: Inter, sans-serif; margin: 40px; color: #111; }
        h1 { font-size: 1.3rem; margin-bottom: 4px; font-family: 'Noto Sans Telugu', sans-serif; }
        .id { font-size: 0.85rem; color: #555; font-family: monospace; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 10px 14px; border: 1px solid #e2e8f0; font-size: 0.95rem; }
        td:first-child { font-weight: 600; color: #374151; width: 40%; background: #f8fafc; }
        .footer { margin-top: 20px; font-size: 0.75rem; color: #9ca3af; }
      </style>
    </head>
    <body>
      <h1>${v.voter_name || '—'}</h1>
      <div class="id">${v.voter_id || '—'}</div>
      <table>
        <tr><td>Voter ID</td><td>${v.voter_id || '—'}</td></tr>
        <tr><td>Serial No.</td><td>${v.full_serial || '—'}</td></tr>
        <tr><td>Age</td><td>${v.age || '—'}</td></tr>
        <tr><td>Gender</td><td>${v.gender || '—'}</td></tr>
        <tr><td>${v.relation_type || 'Relation'}</td><td>${v.relation_name || '—'}</td></tr>
        <tr><td>House Number</td><td>${v.house_number || '—'}</td></tr>
        <tr><td>Part Serial</td><td>${v.part_serial || '—'}</td></tr>
      </table>
      <div class="footer">Sakhavaram Gram Panchayat Voter Roll 2026 — Prakasam District, Andhra Pradesh</div>
    </body>
    </html>
  `);
  printWin.document.close();
  printWin.print();
};

// ========== SHOW ALL ==========
window.showAll = function() {
  searchInput.value = '';
  clearBtn.classList.remove('visible');
  activeFilter = 'all';
  filterChips.forEach(c => c.classList.toggle('active', c.dataset.filter === 'all'));
  ageMinInput.value = '';
  ageMaxInput.value = '';
  filtered = [...allVoters];
  currentPage = 1;
  renderResults('');
};

// ========== CSV EXPORT ==========
function exportCSV() {
  if (!filtered.length) return;
  const headers = ['S.No','Part Serial','Full Serial','Voter Name','Relation Type','Relation Name','Age','Gender','House Number','Voter ID'];
  const rows = filtered.map((v, i) => [
    i + 1, v.part_serial, v.full_serial, v.voter_name,
    v.relation_type, v.relation_name, v.age, v.gender,
    v.house_number, v.voter_id
  ]);
  const csv = [headers, ...rows].map(r =>
    r.map(c => `"${String(c || '').replace(/"/g, '""')}"`).join(',')
  ).join('\n');

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sakhavaram_voters_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ========== UI STATE ==========
function showState(state) {
  stateWelcome.style.display = state === 'welcome' ? 'flex' : 'none';
  stateLoading.style.display = state === 'loading' ? 'flex' : 'none';
  stateEmpty.style.display   = state === 'empty'   ? 'flex' : 'none';
  if (state === 'results') {
    stateWelcome.style.display = 'none';
    stateLoading.style.display = 'none';
    stateEmpty.style.display   = 'none';
  }
}

// ========== EVENT LISTENERS ==========
let searchDebounce;
searchInput.addEventListener('input', () => {
  clearBtn.classList.toggle('visible', searchInput.value.length > 0);
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(runSearch, 280);
});

searchInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { clearTimeout(searchDebounce); runSearch(); }
});

searchBtn.addEventListener('click', () => { clearTimeout(searchDebounce); runSearch(); });

clearBtn.addEventListener('click', () => {
  searchInput.value = '';
  clearBtn.classList.remove('visible');
  showState('welcome');
  resultsBar.style.display = 'none';
  voterGrid.innerHTML = '';
  paginationEl.innerHTML = '';
  searchInput.focus();
});

filterChips.forEach(chip => {
  chip.addEventListener('click', () => {
    filterChips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeFilter = chip.dataset.filter;
    runSearch();
  });
});

[ageMinInput, ageMaxInput].forEach(inp => {
  inp.addEventListener('input', () => { clearTimeout(searchDebounce); searchDebounce = setTimeout(runSearch, 400); });
});

exportBtn.addEventListener('click', exportCSV);

modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// ========== INIT ==========
loadVoters();
