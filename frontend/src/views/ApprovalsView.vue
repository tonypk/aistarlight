<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { approvalsApi, type ApprovalSettings, type ReceiptApproval } from '../api/approvals'

const loading = ref(true)
const settings = ref<ApprovalSettings>({
  is_enabled: false,
  amount_threshold: 10000,
  new_vendor_receipts: 3,
  risk_flags_require_approval: true,
})
const pendingApprovals = ref<ReceiptApproval[]>([])
const allApprovals = ref<ReceiptApproval[]>([])
const pendingTotal = ref(0)
const allTotal = ref(0)
const tab = ref<'pending' | 'history' | 'settings'>('pending')
const savingSettings = ref(false)
const actionLoading = ref<string | null>(null)
const rejectNotes = ref('')
const showRejectModal = ref(false)
const rejectTarget = ref<string | null>(null)

const pendingCount = computed(() => pendingTotal.value)

function triggerLabel(reason: string): string {
  const labels: Record<string, string> = {
    amount_threshold: 'Amount Threshold',
    new_vendor: 'New Vendor',
    risk_flag: 'Risk Flag',
    manual: 'Manual',
  }
  return labels[reason] || reason
}

function triggerClass(reason: string): string {
  const classes: Record<string, string> = {
    amount_threshold: 'badge-amber',
    new_vendor: 'badge-blue',
    risk_flag: 'badge-red',
    manual: 'badge-gray',
  }
  return classes[reason] || 'badge-gray'
}

function statusClass(status: string): string {
  const classes: Record<string, string> = {
    pending: 'status-pending',
    approved: 'status-approved',
    rejected: 'status-rejected',
  }
  return classes[status] || ''
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function parseReceiptSummary(approval: ReceiptApproval): string {
  if (!approval.results) return 'Receipt'
  try {
    const results = typeof approval.results === 'string'
      ? JSON.parse(approval.results)
      : approval.results
    if (Array.isArray(results) && results.length > 0) {
      const p = results[0]?.parsed
      if (p?.vendor_name?.value) return String(p.vendor_name.value)
    }
  } catch { /* ignore */ }
  return 'Receipt'
}

function parseReceiptAmount(approval: ReceiptApproval): string {
  if (!approval.results) return ''
  try {
    const results = typeof approval.results === 'string'
      ? JSON.parse(approval.results)
      : approval.results
    if (Array.isArray(results) && results.length > 0) {
      const p = results[0]?.parsed
      if (p?.total_amount?.value != null) {
        return parseFloat(String(p.total_amount.value)).toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      }
    }
  } catch { /* ignore */ }
  return ''
}

async function fetchData() {
  loading.value = true
  try {
    const [settingsRes, pendingRes, allRes] = await Promise.all([
      approvalsApi.getSettings(),
      approvalsApi.listPending(1, 50),
      approvalsApi.listAll(1, 50),
    ])
    settings.value = settingsRes.data.data
    pendingApprovals.value = pendingRes.data.data || []
    pendingTotal.value = pendingRes.data.meta?.total || 0
    allApprovals.value = allRes.data.data || []
    allTotal.value = allRes.data.meta?.total || 0
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    const res = await approvalsApi.updateSettings(settings.value)
    settings.value = res.data.data
  } catch { /* handled */ }
  finally { savingSettings.value = false }
}

async function approveItem(id: string) {
  actionLoading.value = id
  try {
    await approvalsApi.approve(id)
    await fetchData()
  } catch { /* handled */ }
  finally { actionLoading.value = null }
}

function openRejectModal(id: string) {
  rejectTarget.value = id
  rejectNotes.value = ''
  showRejectModal.value = true
}

async function confirmReject() {
  if (!rejectTarget.value) return
  actionLoading.value = rejectTarget.value
  showRejectModal.value = false
  try {
    await approvalsApi.reject(rejectTarget.value, rejectNotes.value || undefined)
    await fetchData()
  } catch { /* handled */ }
  finally {
    actionLoading.value = null
    rejectTarget.value = null
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="approvals-page">
    <div class="page-header">
      <h2>Receipt Approvals</h2>
      <div v-if="pendingCount > 0" class="pending-badge">{{ pendingCount }} pending</div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: tab === 'pending' }" @click="tab = 'pending'">
        Pending <span v-if="pendingCount" class="tab-count">{{ pendingCount }}</span>
      </button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'">History</button>
      <button :class="{ active: tab === 'settings' }" @click="tab = 'settings'">Settings</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <!-- Pending Tab -->
    <div v-else-if="tab === 'pending'" class="tab-content">
      <div v-if="!pendingApprovals.length" class="empty-state">
        No pending approvals
      </div>
      <div v-else class="approval-list">
        <div v-for="a in pendingApprovals" :key="a.id" class="approval-card">
          <div class="approval-header">
            <div class="approval-vendor">{{ parseReceiptSummary(a) }}</div>
            <span :class="['trigger-badge', triggerClass(a.trigger_reason)]">
              {{ triggerLabel(a.trigger_reason) }}
            </span>
          </div>
          <div class="approval-details">
            <span v-if="parseReceiptAmount(a)" class="detail-amount">{{ parseReceiptAmount(a) }}</span>
            <span class="detail-period">{{ a.period }}</span>
            <span class="detail-date">{{ formatDate(a.created_at) }}</span>
          </div>
          <div class="approval-actions">
            <button
              class="btn-approve"
              :disabled="actionLoading === a.id"
              @click="approveItem(a.id)"
            >
              {{ actionLoading === a.id ? '...' : 'Approve' }}
            </button>
            <button
              class="btn-reject"
              :disabled="actionLoading === a.id"
              @click="openRejectModal(a.id)"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- History Tab -->
    <div v-else-if="tab === 'history'" class="tab-content">
      <div v-if="!allApprovals.length" class="empty-state">No approval history</div>
      <table v-else class="history-table">
        <thead>
          <tr>
            <th>Receipt</th>
            <th>Amount</th>
            <th>Reason</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in allApprovals" :key="a.id">
            <td>{{ parseReceiptSummary(a) }}</td>
            <td class="col-amount">{{ parseReceiptAmount(a) }}</td>
            <td><span :class="['trigger-badge', triggerClass(a.trigger_reason)]">{{ triggerLabel(a.trigger_reason) }}</span></td>
            <td><span :class="['status-badge', statusClass(a.status)]">{{ a.status }}</span></td>
            <td class="col-date">{{ formatDate(a.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Settings Tab -->
    <div v-else-if="tab === 'settings'" class="tab-content">
      <div class="settings-card">
        <div class="setting-row">
          <label class="setting-label">
            <input type="checkbox" v-model="settings.is_enabled" />
            Enable receipt approval workflow
          </label>
          <p class="setting-desc">When enabled, receipts matching the rules below will require approval before processing.</p>
        </div>

        <div class="setting-row">
          <label class="setting-label">Amount threshold</label>
          <div class="setting-input-group">
            <input type="number" v-model.number="settings.amount_threshold" min="0" step="100" :disabled="!settings.is_enabled" />
            <p class="setting-desc">Receipts above this amount require approval.</p>
          </div>
        </div>

        <div class="setting-row">
          <label class="setting-label">New vendor check</label>
          <div class="setting-input-group">
            <input type="number" v-model.number="settings.new_vendor_receipts" min="0" max="20" :disabled="!settings.is_enabled" />
            <p class="setting-desc">First N receipts from a new vendor require approval (0 = disabled).</p>
          </div>
        </div>

        <div class="setting-row">
          <label class="setting-label">
            <input type="checkbox" v-model="settings.risk_flags_require_approval" :disabled="!settings.is_enabled" />
            Risk flags require approval
          </label>
          <p class="setting-desc">Duplicate images and other risk flags will trigger approval.</p>
        </div>

        <button class="btn-save" :disabled="savingSettings" @click="saveSettings">
          {{ savingSettings ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="modal-overlay" @click.self="showRejectModal = false">
      <div class="modal-content">
        <h3>Reject Receipt</h3>
        <textarea v-model="rejectNotes" placeholder="Reason for rejection (optional)" rows="3"></textarea>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showRejectModal = false">Cancel</button>
          <button class="btn-reject" @click="confirmReject">Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.approvals-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.pending-badge {
  background: #ef4444;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 2px solid var(--border-default);
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tabs button.active {
  color: var(--brand-primary);
  border-bottom-color: var(--brand-primary);
  font-weight: 600;
}

.tab-count {
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  margin-left: 4px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-muted);
}

/* Approval Cards */
.approval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.approval-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
}

.approval-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.approval-vendor {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.trigger-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-amber { background: #fef3c7; color: #92400e; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-gray { background: var(--bg-surface-hover); color: var(--text-primary); }

.approval-details {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-amount {
  font-weight: 600;
  color: var(--text-primary);
}

.approval-actions {
  display: flex;
  gap: 8px;
}

.btn-approve {
  padding: 6px 16px;
  background: #22c55e;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.btn-approve:hover { background: #16a34a; }
.btn-approve:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-reject {
  padding: 6px 16px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.btn-reject:hover { background: #dc2626; }
.btn-reject:disabled { opacity: 0.5; cursor: not-allowed; }

/* History Table */
.history-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  overflow: hidden;
}

.history-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-surface-alt);
  border-bottom: 1px solid var(--border-default);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-table td {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid #f3f4f6;
}

.col-amount { font-weight: 600; text-align: right; }
.col-date { color: var(--text-secondary); white-space: nowrap; }

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: capitalize;
}

.status-pending { background: #fef3c7; color: #92400e; }
.status-approved { background: #dcfce7; color: #166534; }
.status-rejected { background: #fee2e2; color: #991b1b; }

/* Settings */
.settings-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 24px;
}

.setting-row {
  margin-bottom: 20px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.setting-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--brand-primary);
}

.setting-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.setting-input-group input[type="number"] {
  width: 120px;
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 4px;
}

.setting-input-group input:disabled {
  background: var(--bg-surface-alt);
  color: var(--text-muted);
}

.btn-save {
  padding: 8px 24px;
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  margin-top: 8px;
}

.btn-save:hover { background: var(--brand-primary-hover); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* Reject Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.modal-content h3 {
  margin: 0 0 12px;
  color: var(--text-primary);
}

.modal-content textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.btn-cancel {
  padding: 6px 16px;
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

@media (max-width: 768px) {
  .approval-details {
    flex-direction: column;
    gap: 4px;
  }

  .history-table { font-size: 12px; }
  .history-table th, .history-table td { padding: 8px; }
}
</style>
