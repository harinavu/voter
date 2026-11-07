/**
 * auth.js — Client-side login for Sakhavaram Voter Search
 *
 * To change the password:
 *   Run:  python3 change_password.py
 *   Then update AUTH_PASSWORD_HASH below with the printed hash.
 */

'use strict';

// ── CONFIG ────────────────────────────────────────────────────────────────────
const AUTH_USERNAME      = 'harinavu999';
const AUTH_PASSWORD_HASH = '3e8d74c00a8d90e9a23ffe1ab093c7576c971c76f06d6d22c3b42b0fb9ea65ee';
const SESSION_KEY        = 'voter_auth_session';
const SESSION_DURATION   = 8 * 60 * 60 * 1000; // 8 hours in ms

// ── HELPERS ───────────────────────────────────────────────────────────────────
async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

function saveSession() {
  const session = { expires: Date.now() + SESSION_DURATION };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function isSessionValid() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return false;
    const { expires } = JSON.parse(raw);
    return Date.now() < expires;
  } catch {
    return false;
  }
}

function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
}

// ── RENDER LOGIN OVERLAY ──────────────────────────────────────────────────────
function renderLoginOverlay() {
  const overlay = document.getElementById('loginOverlay');
  if (!overlay) return;
  overlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  const form       = document.getElementById('loginForm');
  const userInput  = document.getElementById('loginUsername');
  const passInput  = document.getElementById('loginPassword');
  const loginBtn   = document.getElementById('loginBtn');
  const loginError = document.getElementById('loginError');
  const toggleBtn  = document.getElementById('togglePassword');
  const spinner    = document.getElementById('loginSpinner');

  // Toggle password visibility
  toggleBtn.addEventListener('click', () => {
    const isText = passInput.type === 'text';
    passInput.type = isText ? 'password' : 'text';
    toggleBtn.textContent = isText ? '👁' : '🙈';
  });

  async function attemptLogin(e) {
    e.preventDefault();
    loginError.style.display = 'none';
    loginBtn.disabled = true;
    spinner.style.display = 'inline-block';

    const username = userInput.value.trim();
    const password = passInput.value;

    // Small delay so spinner is visible
    await new Promise(r => setTimeout(r, 400));

    const hash = await sha256(password);
    const valid = username === AUTH_USERNAME && hash === AUTH_PASSWORD_HASH;

    if (valid) {
      saveSession();
      // Show logout button
      const logoutBtn = document.getElementById('logoutBtn');
      if (logoutBtn) logoutBtn.style.display = 'inline-flex';
      overlay.classList.add('auth-fade-out');
      setTimeout(() => {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
      }, 600);
    } else {
      loginBtn.disabled = false;
      spinner.style.display = 'none';
      loginError.style.display = 'block';
      // Shake animation
      form.classList.add('auth-shake');
      passInput.value = '';
      setTimeout(() => form.classList.remove('auth-shake'), 500);
    }
  }

  form.addEventListener('submit', attemptLogin);
  userInput.focus();
}

// ── LOGOUT ────────────────────────────────────────────────────────────────────
window.logoutUser = function () {
  clearSession();
  location.reload();
};

// ── INIT ──────────────────────────────────────────────────────────────────────
(function init() {
  if (!isSessionValid()) {
    // Block until DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderLoginOverlay);
    } else {
      renderLoginOverlay();
    }
  } else {
    // Session is valid – show the logout button immediately
    document.addEventListener('DOMContentLoaded', () => {
      const btn = document.getElementById('logoutBtn');
      if (btn) btn.style.display = 'inline-flex';
    });
  }
})();
