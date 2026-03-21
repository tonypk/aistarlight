<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { invoiceApi } from '../api/invoices'
import type { Invoice, InvoiceWithItems, CreateInvoiceRequest } from '../api/invoices'

const { t } = useI18n()

// State
const invoices = ref<Invoice[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)
const error = ref('')

// Filters
const filterStatus = ref('')
const filterType = ref('')

// Detail / form state
const showDetail = ref(false)
const showForm = ref(false)
const selectedInvoice = ref<InvoiceWithItems | null>(null)
const detailLoading = ref(false)

// Form data
const form = ref<CreateInvoiceRequest>({
  invoice_type: 'sales',
  customer_name: '',
  customer_tin: '',
  customer_address: '',
  invoice_date: new Date().toISOString().slice(0, 10),
  due_date: '',
  reference_number: '',
  notes: '',
  items: [{ description: '', quantity: 1, unit_price: 0, vat_type: 'vatable', vat_rate: 12, discount: 0, atc_code: '' }],
})

const totalPages = computed(() => Math.ceil(total.value / limit.value))

const formTotals = computed(() => {
  let subtotal = 0, vatAmount = 0, discountTotal = 0
  for (const item of form.value.items) {
    const lineNet = (item.quantity || 1) * (item.unit_price || 0) - (item.discount || 0)
    subtotal += lineNet
    discountTotal += item.discount || 0
    if (item.vat_type === 'vatable') {
      vatAmount += lineNet * (item.vat_rate || 12) / 100
    }
  }
  return { subtotal, vatAmount, discountTotal, total: subtotal + vatAmount }
})

onMounted(() => fetchInvoices())

async function fetchInvoices() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await invoiceApi.list(page.value, limit.value, filterStatus.value || undefined, filterType.value || undefined)
    invoices.value = data.data || []
    total.value = data.meta?.total ?? 0
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.loadFailed')
  } finally {
    loading.value = false
  }
}

async function viewInvoice(id: string) {
  detailLoading.value = true
  showDetail.value = true
  try {
    const { data } = await invoiceApi.get(id)
    selectedInvoice.value = data.data
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.loadDetailFailed')
    showDetail.value = false
  } finally {
    detailLoading.value = false
  }
}

function openCreate() {
  form.value = {
    invoice_type: 'sales',
    customer_name: '',
    customer_tin: '',
    customer_address: '',
    invoice_date: new Date().toISOString().slice(0, 10),
    due_date: '',
    reference_number: '',
    notes: '',
    items: [{ description: '', quantity: 1, unit_price: 0, vat_type: 'vatable', vat_rate: 12, discount: 0, atc_code: '' }],
  }
  showForm.value = true
}

function addItem() {
  form.value.items.push({ description: '', quantity: 1, unit_price: 0, vat_type: 'vatable', vat_rate: 12, discount: 0, atc_code: '' })
}

function removeItem(index: number) {
  if (form.value.items.length > 1) {
    form.value.items.splice(index, 1)
  }
}

async function submitInvoice() {
  if (!form.value.customer_name || !form.value.invoice_date) {
    error.value = t('invoice.customerRequired')
    return
  }
  if (form.value.items.length === 0 || !form.value.items[0].description) {
    error.value = t('invoice.itemRequired')
    return
  }
  loading.value = true
  error.value = ''
  try {
    await invoiceApi.create(form.value)
    showForm.value = false
    await fetchInvoices()
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.createFailed')
  } finally {
    loading.value = false
  }
}

async function updateStatus(id: string, status: string) {
  try {
    await invoiceApi.updateStatus(id, status)
    await fetchInvoices()
    if (selectedInvoice.value?.invoice?.id === id) {
      await viewInvoice(id)
    }
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.statusUpdateFailed')
  }
}

async function deleteInvoice(id: string) {
  if (!confirm(t('invoice.deleteConfirm'))) return
  try {
    await invoiceApi.delete(id)
    showDetail.value = false
    selectedInvoice.value = null
    await fetchInvoices()
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.deleteFailed')
  }
}

async function exportEIS(id: string, invoiceNumber: string) {
  try {
    const { data } = await invoiceApi.exportEIS(id)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `EIS_${invoiceNumber}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? t('invoice.exportFailed')
  }
}

function formatMoney(v: any): string {
  const n = Number(v) || 0
  return n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { draft: t('invoice.draft'), sent: t('invoice.sent'), paid: t('invoice.paid'), cancelled: t('invoice.cancelled'), overdue: t('invoice.overdue') }
  return map[s] || s
}

function statusClass(s: string): string {
  const map: Record<string, string> = { draft: 'badge-gray', sent: 'badge-blue', paid: 'badge-green', cancelled: 'badge-red', overdue: 'badge-orange' }
  return map[s] || 'badge-gray'
}

function typeLabel(tp: string): string {
  const map: Record<string, string> = { sales: t('invoice.sales'), purchase: t('invoice.purchase'), credit_note: t('invoice.creditNote'), debit_note: t('invoice.debitNote') }
  return map[tp] || tp
}

function changePage(p: number) {
  page.value = p
  fetchInvoices()
}
</script>

<template>
  <div class="invoice-view">
    <div class="view-header">
      <h2>{{ t('invoice.title') }}</h2>
      <button class="btn primary" @click="openCreate">{{ t('invoice.newInvoice') }}</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Filters -->
    <div class="filters">
      <select v-model="filterStatus" @change="fetchInvoices()">
        <option value="">{{ t('invoice.allStatuses') }}</option>
        <option value="draft">{{ t('invoice.draft') }}</option>
        <option value="sent">{{ t('invoice.sent') }}</option>
        <option value="paid">{{ t('invoice.paid') }}</option>
        <option value="cancelled">{{ t('invoice.cancelled') }}</option>
        <option value="overdue">{{ t('invoice.overdue') }}</option>
      </select>
      <select v-model="filterType" @change="fetchInvoices()">
        <option value="">{{ t('invoice.allTypes') }}</option>
        <option value="sales">{{ t('invoice.sales') }}</option>
        <option value="purchase">{{ t('invoice.purchase') }}</option>
        <option value="credit_note">{{ t('invoice.creditNote') }}</option>
        <option value="debit_note">{{ t('invoice.debitNote') }}</option>
      </select>
    </div>

    <!-- Invoice List -->
    <div v-if="loading && invoices.length === 0" class="loading">{{ t('invoice.loading') }}</div>
    <table v-else-if="invoices.length" class="data-table">
      <thead>
        <tr>
          <th>{{ t('invoice.thInvoiceNum') }}</th>
          <th>{{ t('invoice.thType') }}</th>
          <th>{{ t('invoice.thCustomer') }}</th>
          <th>{{ t('invoice.thDate') }}</th>
          <th>{{ t('invoice.thTotal') }}</th>
          <th>{{ t('invoice.thStatus') }}</th>
          <th>{{ t('invoice.thEIS') }}</th>
          <th>{{ t('invoice.thActions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inv in invoices" :key="inv.id" @click="viewInvoice(inv.id)" class="clickable">
          <td class="mono">{{ inv.invoice_number }}</td>
          <td>{{ typeLabel(inv.invoice_type) }}</td>
          <td>{{ inv.customer_name }}</td>
          <td>{{ inv.invoice_date?.slice(0, 10) }}</td>
          <td class="money">PHP {{ formatMoney(inv.total_amount) }}</td>
          <td><span :class="['badge', statusClass(inv.status)]">{{ statusLabel(inv.status) }}</span></td>
          <td><span :class="['badge', inv.eis_status === 'submitted' ? 'badge-green' : 'badge-gray']">{{ inv.eis_status || t('invoice.notSubmitted') }}</span></td>
          <td class="actions" @click.stop>
            <button class="btn-sm" @click="exportEIS(inv.id, inv.invoice_number)" :title="t('invoice.exportEIS')">{{ t('invoice.eis') }}</button>
            <button v-if="inv.status === 'draft'" class="btn-sm" @click="updateStatus(inv.id, 'sent')">{{ t('invoice.send') }}</button>
            <button v-if="inv.status === 'sent'" class="btn-sm success" @click="updateStatus(inv.id, 'paid')">{{ t('invoice.markPaid') }}</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">{{ t('invoice.empty') }}</div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="changePage(page - 1)">{{ t('common.prev') }}</button>
      <span>{{ t('common.page', { page, total: totalPages }) }}</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">{{ t('common.next') }}</button>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal wide">
        <div class="modal-header">
          <h3>{{ t('invoice.invoiceDetail', { number: selectedInvoice?.invoice?.invoice_number }) }}</h3>
          <button class="close-btn" @click="showDetail = false">x</button>
        </div>
        <div v-if="detailLoading" class="loading">{{ t('invoice.loading') }}</div>
        <div v-else-if="selectedInvoice" class="invoice-detail">
          <div class="detail-grid">
            <div><strong>{{ t('invoice.type') }}</strong> {{ typeLabel(selectedInvoice.invoice.invoice_type) }}</div>
            <div><strong>{{ t('invoice.status') }}</strong> <span :class="['badge', statusClass(selectedInvoice.invoice.status)]">{{ statusLabel(selectedInvoice.invoice.status) }}</span></div>
            <div><strong>{{ t('invoice.date') }}</strong> {{ selectedInvoice.invoice.invoice_date?.slice(0, 10) }}</div>
            <div><strong>{{ t('invoice.due') }}</strong> {{ selectedInvoice.invoice.due_date?.slice(0, 10) || '-' }}</div>
            <div><strong>{{ t('invoice.customer') }}</strong> {{ selectedInvoice.invoice.customer_name }}</div>
            <div><strong>{{ t('invoice.tin') }}</strong> {{ selectedInvoice.invoice.customer_tin || '-' }}</div>
            <div class="full-width"><strong>{{ t('invoice.address') }}</strong> {{ selectedInvoice.invoice.customer_address || '-' }}</div>
            <div v-if="selectedInvoice.invoice.reference_number" class="full-width"><strong>{{ t('invoice.ref') }}</strong> {{ selectedInvoice.invoice.reference_number }}</div>
          </div>

          <h4>{{ t('invoice.lineItems') }}</h4>
          <table class="data-table compact">
            <thead>
              <tr><th>{{ t('invoice.thLineNum') }}</th><th>{{ t('invoice.thDescription') }}</th><th>{{ t('invoice.thQty') }}</th><th>{{ t('invoice.thUnitPrice') }}</th><th>{{ t('invoice.thAmount') }}</th><th>{{ t('invoice.thVatType') }}</th><th>{{ t('invoice.thVat') }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedInvoice.items" :key="item.line_number">
                <td>{{ item.line_number }}</td>
                <td>{{ item.description }}</td>
                <td class="money">{{ formatMoney(item.quantity) }}</td>
                <td class="money">{{ formatMoney(item.unit_price) }}</td>
                <td class="money">{{ formatMoney(item.amount) }}</td>
                <td>{{ item.vat_type }}</td>
                <td class="money">{{ formatMoney(item.vat_amount) }}</td>
              </tr>
            </tbody>
          </table>

          <div class="totals-grid">
            <div><strong>{{ t('invoice.subtotal') }}</strong> PHP {{ formatMoney(selectedInvoice.invoice.subtotal) }}</div>
            <div><strong>{{ t('invoice.vat') }}</strong> PHP {{ formatMoney(selectedInvoice.invoice.vat_amount) }}</div>
            <div><strong>{{ t('invoice.discount') }}</strong> PHP {{ formatMoney(selectedInvoice.invoice.discount_amount) }}</div>
            <div class="total-row"><strong>{{ t('invoice.total') }}</strong> PHP {{ formatMoney(selectedInvoice.invoice.total_amount) }}</div>
          </div>

          <div class="vat-breakdown">
            <span>{{ t('invoice.vatableSales') }} PHP {{ formatMoney(selectedInvoice.invoice.vatable_sales) }}</span>
            <span>{{ t('invoice.vatExemptSales') }} PHP {{ formatMoney(selectedInvoice.invoice.vat_exempt_sales) }}</span>
            <span>{{ t('invoice.zeroRatedSales') }} PHP {{ formatMoney(selectedInvoice.invoice.zero_rated_sales) }}</span>
          </div>

          <div v-if="selectedInvoice.invoice.notes" class="notes">
            <strong>{{ t('invoice.notes') }}</strong> {{ selectedInvoice.invoice.notes }}
          </div>

          <div class="detail-actions">
            <button class="btn" @click="exportEIS(selectedInvoice.invoice.id, selectedInvoice.invoice.invoice_number)">{{ t('invoice.exportEIS') }}</button>
            <button v-if="selectedInvoice.invoice.status === 'draft'" class="btn primary" @click="updateStatus(selectedInvoice.invoice.id, 'sent')">{{ t('invoice.markAsSent') }}</button>
            <button v-if="selectedInvoice.invoice.status === 'sent'" class="btn success" @click="updateStatus(selectedInvoice.invoice.id, 'paid')">{{ t('invoice.markAsPaid') }}</button>
            <button v-if="selectedInvoice.invoice.status === 'draft'" class="btn danger" @click="deleteInvoice(selectedInvoice.invoice.id)">{{ t('invoice.deleteInvoice') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Invoice Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal wide">
        <div class="modal-header">
          <h3>{{ t('invoice.newInvoiceForm') }}</h3>
          <button class="close-btn" @click="showForm = false">x</button>
        </div>

        <form @submit.prevent="submitInvoice" class="invoice-form">
          <div class="form-grid">
            <div class="form-group">
              <label>{{ t('invoice.invoiceType') }}</label>
              <select v-model="form.invoice_type">
                <option value="sales">{{ t('invoice.salesInvoice') }}</option>
                <option value="purchase">{{ t('invoice.purchaseInvoice') }}</option>
                <option value="credit_note">{{ t('invoice.creditNote') }}</option>
                <option value="debit_note">{{ t('invoice.debitNote') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ t('invoice.invoiceDate') }}</label>
              <input type="date" v-model="form.invoice_date" required />
            </div>
            <div class="form-group">
              <label>{{ t('invoice.dueDate') }}</label>
              <input type="date" v-model="form.due_date" />
            </div>
            <div class="form-group">
              <label>{{ t('invoice.referenceNum') }}</label>
              <input v-model="form.reference_number" :placeholder="t('invoice.optional')" />
            </div>
          </div>

          <div class="form-grid">
            <div class="form-group">
              <label>{{ t('invoice.customerName') }}</label>
              <input v-model="form.customer_name" required :placeholder="t('invoice.customerNamePlaceholder')" />
            </div>
            <div class="form-group">
              <label>{{ t('invoice.customerTIN') }}</label>
              <input v-model="form.customer_tin" :placeholder="t('invoice.tinPlaceholder')" />
            </div>
            <div class="form-group full-width">
              <label>{{ t('invoice.customerAddress') }}</label>
              <input v-model="form.customer_address" :placeholder="t('invoice.addressPlaceholder')" />
            </div>
          </div>

          <h4>{{ t('invoice.lineItems') }}</h4>
          <table class="data-table compact items-table">
            <thead>
              <tr>
                <th>{{ t('invoice.thDescription') }}</th>
                <th>{{ t('invoice.thQty') }}</th>
                <th>{{ t('invoice.thUnitPrice') }}</th>
                <th>{{ t('invoice.thVatType') }}</th>
                <th>{{ t('invoice.vatPercent') }}</th>
                <th>{{ t('invoice.discountLabel') }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, i) in form.items" :key="i">
                <td><input v-model="item.description" :placeholder="t('invoice.itemDescPlaceholder')" required /></td>
                <td><input type="number" v-model.number="item.quantity" min="0.01" step="0.01" style="width:70px" /></td>
                <td><input type="number" v-model.number="item.unit_price" min="0" step="0.01" style="width:100px" /></td>
                <td>
                  <select v-model="item.vat_type" style="width:110px">
                    <option value="vatable">{{ t('invoice.vatableOption') }}</option>
                    <option value="vat_exempt">{{ t('invoice.vatExemptOption') }}</option>
                    <option value="zero_rated">{{ t('invoice.zeroRatedOption') }}</option>
                  </select>
                </td>
                <td><input type="number" v-model.number="item.vat_rate" min="0" step="0.01" style="width:60px" :disabled="item.vat_type !== 'vatable'" /></td>
                <td><input type="number" v-model.number="item.discount" min="0" step="0.01" style="width:80px" /></td>
                <td><button type="button" class="btn-sm danger" @click="removeItem(i)" :disabled="form.items.length <= 1">-</button></td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="btn-sm" @click="addItem">{{ t('invoice.addItem') }}</button>

          <div class="totals-grid form-totals">
            <div>{{ t('invoice.subtotal') }} PHP {{ formatMoney(formTotals.subtotal) }}</div>
            <div>{{ t('invoice.vat') }} PHP {{ formatMoney(formTotals.vatAmount) }}</div>
            <div>{{ t('invoice.discount') }} PHP {{ formatMoney(formTotals.discountTotal) }}</div>
            <div class="total-row">{{ t('invoice.total') }} PHP {{ formatMoney(formTotals.total) }}</div>
          </div>

          <div class="form-group full-width">
            <label>{{ t('invoice.notesLabel') }}</label>
            <textarea v-model="form.notes" rows="2" :placeholder="t('invoice.notesPlaceholder')"></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="btn" @click="showForm = false">{{ t('invoice.cancel') }}</button>
            <button type="submit" class="btn primary" :disabled="loading">{{ loading ? t('invoice.creating') : t('invoice.createInvoice') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.invoice-view { max-width: 1200px; margin: 0 auto; padding: 1rem; }
.view-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.view-header h2 { margin: 0; }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.filters select { padding: 0.4rem 0.6rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; background: var(--bg-color, #fff); }
.error { color: #dc3545; padding: 0.5rem; background: #fff5f5; border-radius: 4px; }
.loading { text-align: center; padding: 2rem; color: #888; }
.empty { text-align: center; padding: 3rem; color: #888; }

/* Table */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border-color, #eee); }
.data-table th { font-weight: 600; font-size: 0.85rem; color: #666; }
.data-table.compact th, .data-table.compact td { padding: 0.35rem 0.5rem; font-size: 0.9rem; }
.clickable { cursor: pointer; }
.clickable:hover { background: var(--hover-bg, #f8f9fa); }
.mono { font-family: monospace; }
.money { text-align: right; font-variant-numeric: tabular-nums; }
.actions { display: flex; gap: 0.25rem; }

/* Badges */
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.8rem; font-weight: 500; }
.badge-gray { background: #e9ecef; color: #495057; }
.badge-blue { background: #d0ebff; color: #1971c2; }
.badge-green { background: #d3f9d8; color: #2b8a3e; }
.badge-red { background: #ffe0e0; color: #c92a2a; }
.badge-orange { background: #fff3e0; color: #e67700; }

/* Buttons */
.btn { padding: 0.5rem 1rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; cursor: pointer; background: var(--bg-color, #fff); }
.btn.primary { background: #228be6; color: #fff; border-color: #228be6; }
.btn.success { background: #40c057; color: #fff; border-color: #40c057; }
.btn.danger { background: #fa5252; color: #fff; border-color: #fa5252; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-sm { padding: 0.2rem 0.5rem; font-size: 0.85rem; border: 1px solid var(--border-color, #ddd); border-radius: 3px; cursor: pointer; background: var(--bg-color, #f8f9fa); }
.btn-sm.danger { background: #ffe0e0; color: #c92a2a; border-color: #ffc9c9; }
.btn-sm.success { background: #d3f9d8; color: #2b8a3e; border-color: #b2f2bb; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-color, #fff); border-radius: 8px; padding: 1.5rem; max-height: 90vh; overflow-y: auto; width: 90%; max-width: 600px; }
.modal.wide { max-width: 900px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.modal-header h3 { margin: 0; }
.close-btn { background: none; border: none; font-size: 1.2rem; cursor: pointer; padding: 0.25rem 0.5rem; }

/* Detail */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; }
.detail-grid .full-width { grid-column: 1 / -1; }
.totals-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 1rem; padding: 0.75rem; background: var(--hover-bg, #f8f9fa); border-radius: 4px; }
.total-row { font-size: 1.1rem; font-weight: 600; }
.vat-breakdown { display: flex; gap: 1.5rem; margin-top: 0.5rem; font-size: 0.85rem; color: #666; }
.notes { margin-top: 0.75rem; padding: 0.5rem; background: var(--hover-bg, #f8f9fa); border-radius: 4px; }
.detail-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }

/* Form */
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: 0.85rem; font-weight: 500; color: #555; }
.form-group input, .form-group select, .form-group textarea {
  padding: 0.4rem 0.6rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; background: var(--bg-color, #fff);
}
.items-table input, .items-table select { width: 100%; padding: 0.3rem 0.4rem; border: 1px solid var(--border-color, #ddd); border-radius: 3px; }
.form-totals { margin-top: 0.75rem; }
.form-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }

/* Pagination */
.pagination { display: flex; justify-content: center; align-items: center; gap: 1rem; margin-top: 1rem; }
.pagination button { padding: 0.4rem 0.8rem; border: 1px solid var(--border-color, #ddd); border-radius: 4px; cursor: pointer; background: var(--bg-color, #fff); }
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }

h4 { margin: 1rem 0 0.5rem; }

@media (max-width: 768px) {
  .invoice-view { max-width: 100%; padding: 0.5rem; }
  .view-header { flex-direction: column; align-items: flex-start; }
  .detail-grid { grid-template-columns: 1fr; }
  .totals-grid { grid-template-columns: repeat(2, 1fr); }
  .vat-breakdown { flex-direction: column; gap: 0.25rem; }
  .modal.wide { max-width: 95vw; }
  .detail-actions { flex-wrap: wrap; }
  .items-table input,
  .items-table select { min-width: 60px; }
}
</style>
