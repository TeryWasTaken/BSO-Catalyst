/* Campus Calendar — vanilla JS single-page app served by Flask. */
'use strict';

/* ---------- helpers ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const TYPES = {
  event:       { label: 'Event',       plural: 'Events',       color: 'var(--c-event)' },
  assignment:  { label: 'Assignment',  plural: 'Assignments',  color: 'var(--c-assignment)' },
  payment:     { label: 'Payment',     plural: 'Payments',     color: 'var(--c-payment)' },
  recruitment: { label: 'Recruitment', plural: 'Recruitments', color: 'var(--c-recruitment)' },
};
const ICONS = {
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
  shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
  left: '<path d="M15 6l-6 6 6 6"/>',
  right: '<path d="M9 6l6 6-6 6"/>',
};
const icon = (name) => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`;

// The API stores naive UTC datetimes ("2026-10-17T06:00:00"); treat them as UTC.
const parseDate = (s) => new Date(/([zZ]|[+-]\d\d:?\d\d)$/.test(s) ? s : s + 'Z');
const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
const sameDay = (a, b) => startOfDay(a).getTime() === startOfDay(b).getTime();
const dayKey = (d) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
const fmtDate = (d) => d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' });
const fmtTime = (d) => d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
const fmtDateTime = (d) => `${fmtDate(d)}, ${fmtTime(d)}`;
function fmtRange(it) {
  return sameDay(it.start, it.end)
    ? `${fmtDate(it.start)} · ${fmtTime(it.start)} – ${fmtTime(it.end)}`
    : `${fmtDateTime(it.start)} → ${fmtDateTime(it.end)}`;
}
function dueText(it) {
  const now = new Date();
  if (now > it.end) return 'Closed';
  if (now < it.start) return `Opens ${fmtDate(it.start)}`;
  const hrs = Math.round((it.end - now) / 36e5);
  if (hrs < 48) return `Closes in ${hrs}h`;
  return `Closes in ${Math.round(hrs / 24)} days`;
}

/* ---------- state ---------- */
const state = {
  token: localStorage.getItem('token'),
  me: null,
  items: [],
  tab: 'calendar',
  month: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  selected: new Date(),
  filter: 'all',
  authMode: 'login',
  sheet: null,      // item key while the bottom sheet is open
  budget: null,     // { key, html } cache for the payment budget table
  busy: false,
};
const isAdmin = () => state.me?.profile?.User_Authority === 'admin';

/* ---------- API ---------- */
async function api(path, { method = 'GET', body } = {}) {
  const headers = {};
  if (state.token) headers.Authorization = 'Bearer ' + state.token;
  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }
  let res;
  try {
    // Point directly to your deployed Vercel backend
    const API_BASE_URL = 'https://eventcalendar-zeta.vercel.app';
    res = await fetch(API_BASE_URL + path, { method, headers, body });
  } catch {
    throw new Error('Cannot reach the server. Check your connection.');
  }
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON error page */ }
  if (res.status === 413) throw new Error('File is larger than 2 MB.');
  if ((res.status === 401 || res.status === 422) && state.token) {
    logout();
    throw new Error('Session expired. Please sign in again.');
  }
  if (!res.ok) {
    const err = new Error(data?.error || data?.message || 'Request failed');
    err.status = res.status;
    throw err;
  }
  return data;
}

function normalize() {
  const feed = state.feed;
  const out = [];
  feed.events.forEach((o) => out.push({ type: 'event', id: o.Event_ID, name: o.Event_Name, start: parseDate(o.Event_TimeDateStart), end: parseDate(o.Event_TimeDateEnd), desc: o.Event_Desc }));
  feed.recruitments.forEach((o) => out.push({ type: 'recruitment', id: o.Recr_ID, name: o.Recr_Name, start: parseDate(o.Recr_TimeDateStart), end: parseDate(o.Recr_TimeDateEnd), desc: o.Recr_Desc }));
  feed.assignments.forEach((o) => out.push({ type: 'assignment', id: o.Assignment_ID, name: o.Assignment_Name, start: parseDate(o.Assignment_TimeDateStart), end: parseDate(o.Assignment_TimeDateEnd), desc: o.Assignment_Desc, target: o.Target_StudentYear }));
  feed.payments.forEach((o) => out.push({ type: 'payment', id: o.Payment_ID, name: o.Payment_Name, start: parseDate(o.Payment_TimeDateStart), end: parseDate(o.Payment_TimeDateEnd), desc: o.Payment_Desc, target: o.Target_StudentYear, hasBudget: !!o.Budget_Spreadsheet_ID }));
  out.forEach((it) => { it.key = `${it.type}:${it.id}`; });
  state.items = out.sort((a, b) => a.start - b.start);
}

async function loadAll() {
  const [feed, me] = await Promise.all([api('/events/calendar'), api('/users/me')]);
  state.feed = feed;
  state.me = me;
  normalize();
}
async function reloadMe() { state.me = await api('/users/me'); }

/* ---------- submission status (from /users/me) ---------- */
function mine(it) {
  if (!state.me) return null;
  if (it.type === 'assignment') {
    const s = state.me.my_assignments.find((x) => x.assignment_name === it.name);
    return s && { status: s.status, grade: s.grade, feedback: s.feedback, at: s.submitted_at };
  }
  if (it.type === 'payment') {
    const s = state.me.my_payments.find((x) => x.payment_name === it.name);
    return s && { status: s.status, feedback: s.feedback };
  }
  if (it.type === 'recruitment') {
    const s = state.me.my_recruitments.find((x) => x.recruitment_name === it.name);
    return s && { status: s.status, feedback: s.feedback };
  }
  return null;
}
function chipClass(status) {
  if (/verified|graded|accepted/i.test(status)) return 'good';
  if (/reject|declin/i.test(status)) return 'bad';
  return '';
}
const statusChip = (s) => `<span class="chip ${chipClass(s)}">${esc(s)}</span>`;
const SUBMITTABLE = new Set(['assignment', 'payment', 'recruitment']);

/* ---------- views ---------- */
function itemCard(it) {
  const t = TYPES[it.type];
  const m = mine(it);
  const chip = m ? statusChip(m.status) : SUBMITTABLE.has(it.type) ? `<span class="chip neutral">${esc(dueText(it))}</span>` : '';
  return `<button class="card item" style="--tc:${t.color}" data-act="open" data-key="${it.key}">
    <div class="meta"><span class="kind">${t.label}</span>${chip}</div>
    <h3>${esc(it.name)}</h3>
    <div class="when">${esc(fmtRange(it))}</div>
  </button>`;
}

function itemsOnDay(day) {
  const d = startOfDay(day).getTime();
  return state.items.filter((it) => startOfDay(it.start).getTime() <= d && d <= startOfDay(it.end).getTime());
}

function calendarView() {
  const y = state.month.getFullYear();
  const m = state.month.getMonth();
  const offset = (new Date(y, m, 1).getDay() + 6) % 7; // Monday first
  const gridStart = new Date(y, m, 1 - offset);
  const today = new Date();
  let cells = '';
  for (let i = 0; i < 42; i++) {
    const d = addDays(gridStart, i);
    const types = [...new Set(itemsOnDay(d).map((it) => it.type))];
    const cls = ['day', d.getMonth() !== m && 'out', sameDay(d, today) && 'today', sameDay(d, state.selected) && 'sel'].filter(Boolean).join(' ');
    const dots = types.map((t) => `<span class="dot" style="color:${TYPES[t].color}"></span>`).join('');
    cells += `<button class="${cls}" data-act="day" data-day="${d.getFullYear()},${d.getMonth()},${d.getDate()}" aria-label="${esc(d.toDateString())}${types.length ? ', ' + types.length + ' kinds of items' : ''}"><span class="num">${d.getDate()}</span><span class="dots">${dots}</span></button>`;
  }
  const dow = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((n) => `<span>${n}</span>`).join('');
  const legend = Object.values(TYPES).map((t) => `<span><i style="background:${t.color}"></i>${t.label}</span>`).join('');
  const todays = itemsOnDay(state.selected);
  return `
    <div class="card cal">
      <div class="dow">${dow}</div>
      <div class="grid">${cells}</div>
      <div class="legend">${legend}</div>
    </div>
    <div class="section-title"><h2>${esc(state.selected.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }))}</h2><span>${todays.length} item${todays.length === 1 ? '' : 's'}</span></div>
    <div class="list">${todays.length ? todays.map(itemCard).join('') : '<p class="empty">Nothing scheduled this day.</p>'}</div>`;
}

function upcomingView() {
  const filters = [['all', 'All'], ...Object.entries(TYPES).map(([k, v]) => [k, v.plural])];
  const pills = filters.map(([k, label]) => `<button class="pill" data-act="filter" data-filter="${k}" aria-pressed="${state.filter === k}">${label}</button>`).join('');
  const now = new Date();
  const list = state.items.filter((it) => state.filter === 'all' || it.type === state.filter);
  const open = list.filter((it) => it.end >= now).sort((a, b) => a.end - b.end);
  const past = list.filter((it) => it.end < now).sort((a, b) => b.end - a.end);
  return `
    <div class="filters" role="group" aria-label="Filter by type">${pills}</div>
    <div class="section-title" style="margin-top:4px"><h2>Upcoming &amp; open</h2><span>${open.length}</span></div>
    <div class="list">${open.length ? open.map(itemCard).join('') : '<p class="empty">All clear — nothing open.</p>'}</div>
    ${past.length ? `<div class="section-title"><h2>Past</h2><span>${past.length}</span></div><div class="list">${past.map(itemCard).join('')}</div>` : ''}`;
}

function meView() {
  const p = state.me.profile;
  const initials = (p.User_Name || '?').split(/\s+/).slice(0, 2).map((w) => w[0]).join('').toUpperCase();
  const block = (title, rows, nameKey) => `
    <div class="section-title"><h2>${title}</h2><span>${rows.length}</span></div>
    <div class="card">${rows.length ? rows.map((r) => `
      <div class="row"><div class="t"><b>${esc(r[nameKey])}</b>${r.feedback ? `<small>${esc(r.feedback)}</small>` : ''}${r.grade != null ? `<small>Grade: ${esc(r.grade)}</small>` : ''}</div>${statusChip(r.status)}</div>`).join('')
      : '<p class="empty">Nothing submitted yet.</p>'}</div>`;
  return `
    <div class="card who"><div class="avatar">${esc(initials)}</div><div><h2>${esc(p.User_Name)}</h2><p>${esc(p.User_ID)} · ${esc(p.User_Authority)}</p><p>${esc(p.User_Email)}</p></div></div>
    ${block('My assignments', state.me.my_assignments, 'assignment_name')}
    ${block('My payments', state.me.my_payments, 'payment_name')}
    ${block('My recruitment applications', state.me.my_recruitments, 'recruitment_name')}
    <div style="margin-top:24px"><button class="btn ghost" data-act="logout">Sign out</button></div>`;
}

const ADMIN_FORMS = {
  events:      { label: 'Event',       endpoint: '/admin/events',      extras: [] },
  assignments: { label: 'Assignment',  endpoint: '/admin/assignments', extras: ['target'] },
  payments:    { label: 'Payment',     endpoint: '/admin/payments',    extras: ['target', 'sheet'] },
  recruitments:{ label: 'Recruitment', endpoint: '/admin/recruitments',extras: [] },
};
state.adminKind = 'events';

function adminView() {
  const f = ADMIN_FORMS[state.adminKind];
  const opts = Object.entries(ADMIN_FORMS).map(([k, v]) => `<option value="${k}" ${k === state.adminKind ? 'selected' : ''}>${v.label}</option>`).join('');
  return `
    <div class="card panel">
      <form id="admin-form" novalidate>
        <div class="field"><label for="a-kind">What do you want to create?</label><select id="a-kind" data-act="admin-kind">${opts}</select></div>
        <div class="field"><label for="a-name">Name</label><input id="a-name" name="name" required maxlength="150"></div>
        <div class="field"><label for="a-start">Starts</label><input id="a-start" name="start_date" type="datetime-local" required></div>
        <div class="field"><label for="a-end">Ends / deadline</label><input id="a-end" name="end_date" type="datetime-local" required></div>
        ${f.extras.includes('target') ? '<div class="field"><label for="a-target">Target student year <span class="hint">(optional, e.g. 026)</span></label><input id="a-target" name="target_year" maxlength="10"></div>' : ''}
        ${f.extras.includes('sheet') ? '<div class="field"><label for="a-sheet">Budget spreadsheet ID <span class="hint">(optional; the Google Sheet must be public)</span></label><input id="a-sheet" name="spreadsheet_id" maxlength="100" autocapitalize="off" autocomplete="off"></div>' : ''}
        <div class="field"><label for="a-desc">Description <span class="hint">(optional)</span></label><textarea id="a-desc" name="description"></textarea></div>
        <div id="admin-error"></div>
        <button class="btn" type="submit">Create ${f.label.toLowerCase()}</button>
      </form>
    </div>`;
}

function authView() {
  const reg = state.authMode === 'register';
  return `
    <div class="auth">
      <div class="brand">Campus Calendar</div>
      <p class="brand-sub">Events, assignments, payments and recruitment — all in one place.</p>
      <div class="seg" role="group"><button data-act="auth-mode" data-mode="login" aria-pressed="${!reg}">Sign in</button><button data-act="auth-mode" data-mode="register" aria-pressed="${reg}">Create account</button></div>
      <form id="auth-form" novalidate>
        <div id="auth-error"></div>
        <div class="field"><label for="f-id">User ID</label><input id="f-id" name="user_id" autocomplete="username" autocapitalize="characters" required maxlength="20" placeholder="e.g. H1D026052"></div>
        ${reg ? '<div class="field"><label for="f-name">Full name</label><input id="f-name" name="name" autocomplete="name" required maxlength="100"></div>' : ''}
        <div class="field"><label for="f-pw">Password ${reg ? '<span class="hint">(min. 6 characters)</span>' : ''}</label><input id="f-pw" name="password" type="password" autocomplete="${reg ? 'new-password' : 'current-password'}" required></div>
        <button class="btn" type="submit">${reg ? 'Create account' : 'Sign in'}</button>
      </form>
    </div>`;
}

/* ---------- bottom sheet ---------- */
function sheetHtml(it) {
  const t = TYPES[it.type];
  const m = mine(it);
  const canSubmit = SUBMITTABLE.has(it.type);
  const verb = it.type === 'payment' ? 'payment proof' : it.type === 'recruitment' ? 'registration file' : 'assignment file';
  let body = `
    <div class="grab"></div>
    <span class="kind" style="color:${t.color}">${t.label}</span>
    <h2>${esc(it.name)}</h2>
    <dl class="kv">
      <dt>Starts</dt><dd>${esc(fmtDateTime(it.start))}</dd>
      <dt>Ends</dt><dd>${esc(fmtDateTime(it.end))}</dd>
      ${canSubmit ? `<dt>Status</dt><dd>${esc(dueText(it))}</dd>` : ''}
      ${it.target ? `<dt>For year</dt><dd>${esc(it.target)}</dd>` : ''}
    </dl>
    ${it.desc ? `<p class="desc">${esc(it.desc)}</p>` : ''}`;

  if (m) {
    body += `<div class="status-box"><div>Your submission: ${statusChip(m.status)}</div>
      ${m.grade != null ? `<div>Grade: <b>${esc(m.grade)}</b></div>` : ''}
      ${m.feedback ? `<div>Feedback: ${esc(m.feedback)}</div>` : ''}
      ${m.at ? `<div style="color:var(--muted)">Submitted ${esc(fmtDateTime(parseDate(m.at)))}</div>` : ''}</div>`;
  }
  if (canSubmit) {
    body += `<form id="upload-form" data-key="${it.key}" novalidate>
      <div class="field"><label for="u-file">${m ? 'Replace' : 'Upload'} ${verb} <span class="hint">PDF, PNG or JPG · max 2 MB</span></label>
      <input id="u-file" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"></div>
      <div id="upload-error"></div>
      <button class="btn" type="submit">${m ? 'Resubmit' : 'Submit'}</button></form>`;
  }
  if (it.type === 'payment' && it.hasBudget) {
    body += `<div style="margin-top:12px"><button class="btn ghost" data-act="budget" data-key="${it.key}">View budget breakdown</button>
      <div id="budget-out">${state.budget?.key === it.key ? state.budget.html : ''}</div></div>`;
  }
  body += `<div style="margin-top:12px"><button class="btn ghost" data-act="close">Close</button></div>`;
  return `<div class="backdrop" data-act="close"></div><div class="sheet" role="dialog" aria-modal="true" aria-label="${esc(it.name)}">${body}</div>`;
}

function renderSheet() {
  const root = $('#sheet-root');
  const it = state.items.find((x) => x.key === state.sheet);
  root.innerHTML = it ? sheetHtml(it) : '';
  document.body.style.overflow = it ? 'hidden' : '';
}

/* ---------- shell ---------- */
function render() {
  const app = $('#app');
  if (!state.token || !state.me) { app.innerHTML = authView(); renderSheet(); return; }

  const tabs = [['calendar', 'Calendar', 'calendar'], ['upcoming', 'Tasks', 'list'], ['me', 'Me', 'user']];
  if (isAdmin()) tabs.push(['admin', 'Admin', 'shield']);
  const titles = { calendar: state.month.toLocaleDateString(undefined, { month: 'long', year: 'numeric' }), upcoming: 'Tasks', me: 'Me', admin: 'Admin' };
  const nav = state.tab === 'calendar'
    ? `<div class="month-nav"><button class="today-btn" data-act="today">Today</button><button class="icon-btn" data-act="prev" aria-label="Previous month">${icon('left')}</button><button class="icon-btn" data-act="next" aria-label="Next month">${icon('right')}</button></div>` : '';
  const views = { calendar: calendarView, upcoming: upcomingView, me: meView, admin: adminView };

  app.innerHTML = `
    <header class="top"><h1>${esc(titles[state.tab])}</h1>${nav}</header>
    <main>${views[state.tab]()}</main>
    <nav class="tabs" aria-label="Main"><div class="tabs-inner">${tabs.map(([k, label, ic]) => `<button class="tab" data-act="tab" data-tab="${k}" aria-current="${state.tab === k}">${icon(ic)}<span>${label}</span></button>`).join('')}</div></nav>`;
  renderSheet();
}

let toastTimer;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}
const showError = (id, msg) => { const el = $('#' + id); if (el) el.innerHTML = msg ? `<div class="error" role="alert">${esc(msg)}</div>` : ''; };

/* ---------- actions ---------- */
function logout() {
  localStorage.removeItem('token');
  state.token = null; state.me = null; state.items = []; state.sheet = null; state.tab = 'calendar';
  render();
}

async function afterAuth(token) {
  state.token = token;
  localStorage.setItem('token', token);
  await loadAll();
  state.selected = new Date();
  state.month = new Date(state.selected.getFullYear(), state.selected.getMonth(), 1);
  render();
}

document.addEventListener('click', async (e) => {
  const el = e.target.closest('[data-act]');
  if (!el) return;
  const act = el.dataset.act;
  switch (act) {
    case 'tab': state.tab = el.dataset.tab; render(); window.scrollTo(0, 0); break;
    case 'prev': state.month = new Date(state.month.getFullYear(), state.month.getMonth() - 1, 1); render(); break;
    case 'next': state.month = new Date(state.month.getFullYear(), state.month.getMonth() + 1, 1); render(); break;
    case 'today': { const n = new Date(); state.selected = n; state.month = new Date(n.getFullYear(), n.getMonth(), 1); render(); break; }
    case 'day': {
      const [y, m, d] = el.dataset.day.split(',').map(Number);
      state.selected = new Date(y, m, d);
      state.month = new Date(y, m, 1);
      render();
      break;
    }
    case 'filter': state.filter = el.dataset.filter; render(); break;
    case 'open': state.sheet = el.dataset.key; renderSheet(); break;
    case 'close': state.sheet = null; renderSheet(); break;
    case 'logout': logout(); break;
    case 'auth-mode': state.authMode = el.dataset.mode; render(); break;
    case 'budget': await showBudget(el); break;
  }
});

document.addEventListener('change', (e) => {
  if (e.target.dataset.act === 'admin-kind') { state.adminKind = e.target.value; render(); }
});
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && state.sheet) { state.sheet = null; renderSheet(); } });

document.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('button[type=submit]');
  if (btn.disabled) return;
  btn.disabled = true;
  try {
    if (form.id === 'auth-form') await handleAuth(form);
    else if (form.id === 'upload-form') await handleUpload(form);
    else if (form.id === 'admin-form') await handleAdmin(form);
  } finally {
    btn.disabled = false;
  }
});

async function handleAuth(form) {
  const f = new FormData(form);
  const reg = state.authMode === 'register';
  const body = { user_id: f.get('user_id').trim(), password: f.get('password') };
  if (reg) body.name = f.get('name').trim();
  if (!body.user_id || !body.password || (reg && !body.name)) return showError('auth-error', 'Please fill in every field.');
  try {
    const data = await api(reg ? '/auth/register' : '/auth/login', { method: 'POST', body });
    await afterAuth(data.access_token);
  } catch (err) {
    showError('auth-error', err.message);
  }
}

const MAX_BYTES = 2 * 1024 * 1024;
async function handleUpload(form) {
  const it = state.items.find((x) => x.key === form.dataset.key);
  const file = $('#u-file', form).files[0];
  if (!file) return showError('upload-error', 'Choose a file first.');
  if (!/\.(pdf|png|jpe?g)$/i.test(file.name)) return showError('upload-error', 'Only PDF, PNG or JPG files are allowed.');
  if (file.size > MAX_BYTES) return showError('upload-error', 'File is larger than 2 MB.');
  const path = { assignment: 'assignments', payment: 'payments', recruitment: 'recruitments' }[it.type];
  const fd = new FormData();
  fd.append('file', file);
  try {
    await api(`/files/${path}/${it.id}/submit`, { method: 'POST', body: fd });
    await reloadMe();
    toast('Submitted successfully');
    render();
  } catch (err) {
    showError('upload-error', err.message);
  }
}

async function showBudget(btn) {
  const it = state.items.find((x) => x.key === btn.dataset.key);
  const out = $('#budget-out');
  btn.disabled = true;
  out.innerHTML = '<p class="empty">Loading…</p>';
  try {
    const data = await api(`/payments/${it.id}/budget`);
    const rows = data.budget_breakdown || [];
    if (!rows.length) { out.innerHTML = '<p class="empty">The budget sheet is empty.</p>'; }
    else {
      const cols = Object.keys(rows[0]);
      out.innerHTML = `<div class="table-wrap"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${cols.map((c) => `<td>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
    }
    state.budget = { key: it.key, html: out.innerHTML };
  } catch (err) {
    out.innerHTML = `<div class="error">${esc(err.status === 404 ? err.message : 'Could not load the budget. Make sure the Google Sheet is shared publicly.')}</div>`;
  } finally {
    btn.disabled = false;
  }
}

async function handleAdmin(form) {
  const f = new FormData(form);
  const name = f.get('name').trim();
  const start = f.get('start_date');
  const end = f.get('end_date');
  if (!name || !start || !end) return showError('admin-error', 'Name, start and end are required.');
  if (new Date(end) < new Date(start)) return showError('admin-error', 'The end must not be before the start.');
  // datetime-local is in the browser's timezone; send UTC so the server stores it consistently.
  const body = { name, start_date: new Date(start).toISOString(), end_date: new Date(end).toISOString(), description: f.get('description').trim() || null };
  if (f.has('target_year')) body.target_year = f.get('target_year').trim() || null;
  if (f.has('spreadsheet_id')) body.spreadsheet_id = f.get('spreadsheet_id').trim() || null;
  try {
    await api(ADMIN_FORMS[state.adminKind].endpoint, { method: 'POST', body });
    state.feed = await api('/events/calendar');
    normalize();
    toast(`${ADMIN_FORMS[state.adminKind].label} created`);
    render();
  } catch (err) {
    showError('admin-error', err.message);
  }
}

/* ---------- boot ---------- */
(async function init() {
  if (state.token) {
    try { await loadAll(); } catch { /* api() already logged out on 401/422 */ }
  }
  render();
})();
