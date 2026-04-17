const API = '/api';

// ── Navigation ──────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = link.dataset.section;
    document.querySelectorAll('.nav-item').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    link.classList.add('active');
    document.getElementById(`section-${target}`).classList.add('active');
    if (target === 'overview') loadOverview();
    if (target === 'transactions') loadTransactions();
    if (target === 'analytics') loadAnalytics();
  });
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function statusBadge(status) {
  return `<span class="badge-status badge-${status}">${status}</span>`;
}

function fmt(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ── Overview ─────────────────────────────────────────────────────────────────
async function loadOverview() {
  try {
    const summary = await apiFetch('/analytics/summary');
    document.getElementById('totalVolume').textContent = fmt(summary.total_volume_usd);
    document.getElementById('countSucceeded').textContent = summary.counts.succeeded ?? 0;
    document.getElementById('countFailed').textContent    = summary.counts.failed    ?? 0;
    document.getElementById('countRefunded').textContent  = summary.counts.refunded  ?? 0;
  } catch (e) {
    console.error('Summary fetch failed', e);
  }

  try {
    const txs = await apiFetch('/transactions/?limit=5');
    const tbody = document.getElementById('recentBody');
    tbody.innerHTML = txs.length
      ? txs.map(tx => `
          <tr>
            <td>#${tx.id}</td>
            <td>${tx.customer_email}</td>
            <td>${fmt(tx.amount, tx.currency)}</td>
            <td>${statusBadge(tx.status)}</td>
            <td>${tx.status === 'succeeded'
              ? `<button class="btn-link" onclick="refund(${tx.id})">Refund</button>`
              : '—'}</td>
          </tr>`).join('')
      : '<tr><td colspan="5" class="loading">No transactions yet.</td></tr>';
  } catch (e) {
    document.getElementById('recentBody').innerHTML =
      '<tr><td colspan="5" class="loading">Failed to load transactions.</td></tr>';
  }
}

// ── Transactions ──────────────────────────────────────────────────────────────
async function loadTransactions() {
  try {
    const txs = await apiFetch('/transactions/');
    const tbody = document.getElementById('txBody');
    tbody.innerHTML = txs.length
      ? txs.map(tx => `
          <tr>
            <td>#${tx.id}</td>
            <td>${tx.customer_email}</td>
            <td>${fmt(tx.amount, tx.currency)}</td>
            <td>${tx.currency}</td>
            <td>${statusBadge(tx.status)}</td>
            <td>${tx.description ?? '—'}</td>
            <td>${tx.status === 'succeeded'
              ? `<button class="btn-link" onclick="refund(${tx.id})">Refund</button>`
              : '—'}</td>
          </tr>`).join('')
      : '<tr><td colspan="7" class="loading">No transactions.</td></tr>';
  } catch (e) {
    document.getElementById('txBody').innerHTML =
      '<tr><td colspan="7" class="loading">Failed to load.</td></tr>';
  }
}

// ── New charge form ───────────────────────────────────────────────────────────
document.getElementById('newChargeBtn').addEventListener('click', () => {
  document.getElementById('chargeForm').classList.toggle('hidden');
});
document.getElementById('cancelChargeBtn').addEventListener('click', () => {
  document.getElementById('chargeForm').classList.add('hidden');
});
document.getElementById('chargeFormEl').addEventListener('submit', async e => {
  e.preventDefault();
  const body = {
    customer_email: document.getElementById('fEmail').value,
    amount: parseFloat(document.getElementById('fAmount').value),
    description: document.getElementById('fDesc').value,
  };
  try {
    await apiFetch('/transactions/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    document.getElementById('chargeForm').classList.add('hidden');
    document.getElementById('chargeFormEl').reset();
    await loadTransactions();
  } catch (e) {
    alert(`Charge failed: ${e.message}`);
  }
});

// ── Refund ────────────────────────────────────────────────────────────────────
async function refund(id) {
  if (!confirm(`Refund transaction #${id}?`)) return;
  try {
    await apiFetch(`/transactions/${id}/refund`, { method: 'POST' });
    loadOverview();
    loadTransactions();
  } catch (e) {
    alert(`Refund failed: ${e.message}`);
  }
}

// ── Analytics ─────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const rev = await apiFetch('/analytics/revenue');
    document.getElementById('revenueJson').textContent = JSON.stringify(rev, null, 2);
  } catch (e) {
    document.getElementById('revenueJson').textContent = `Error: ${e.message}`;
  }
  try {
    const cust = await apiFetch('/analytics/customers');
    document.getElementById('customerJson').textContent = JSON.stringify(cust, null, 2);
  } catch (e) {
    document.getElementById('customerJson').textContent = `Error: ${e.message}`;
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadOverview();
