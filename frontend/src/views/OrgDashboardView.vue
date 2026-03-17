<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import {
  orgApi,
  type OrgDashboardData,
  type Organization,
  type BatchComplianceResult,
} from "../api/org";

const router = useRouter();
const auth = useAuthStore();

const orgs = ref<Organization[]>([]);
const selectedOrgId = ref("");
const dashboard = ref<OrgDashboardData | null>(null);
const loading = ref(false);
const batchLoading = ref(false);
const batchResult = ref<BatchComplianceResult | null>(null);
const error = ref("");

const hasOrgs = computed(() => orgs.value.length > 0);

async function loadOrgs() {
  try {
    const res = await orgApi.list();
    orgs.value = res.data.data || [];
    if (orgs.value.length > 0 && !selectedOrgId.value) {
      selectedOrgId.value = orgs.value[0].id;
      await loadDashboard();
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load organizations";
  }
}

async function loadDashboard() {
  if (!selectedOrgId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const res = await orgApi.dashboard(selectedOrgId.value);
    dashboard.value = res.data.data;
    batchResult.value = null;
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load dashboard";
  } finally {
    loading.value = false;
  }
}

async function runBatchCompliance() {
  if (!selectedOrgId.value) return;
  batchLoading.value = true;
  try {
    const res = await orgApi.batchComplianceCheck(selectedOrgId.value);
    batchResult.value = res.data.data;
    await loadDashboard();
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Batch check failed";
  } finally {
    batchLoading.value = false;
  }
}

function switchToCompany(companyId: string) {
  auth.switchCompany(companyId);
  router.push("/");
}

function fmt(val: string | number): string {
  const n = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(n)) return "0.00";
  return n.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

onMounted(loadOrgs);
</script>

<template>
  <div class="org-dashboard">
    <div class="view-header">
      <h1>Organization Dashboard</h1>
      <div class="header-actions">
        <select
          v-if="orgs.length > 1"
          v-model="selectedOrgId"
          @change="loadDashboard"
          class="org-select"
        >
          <option v-for="org in orgs" :key="org.id" :value="org.id">
            {{ org.name }}
          </option>
        </select>
        <router-link to="/org-manage" class="btn btn-outline">
          Manage Organization
        </router-link>
      </div>
    </div>

    <div v-if="!hasOrgs && !loading" class="empty-state">
      <h3>No Organization Found</h3>
      <p>
        You are not part of any organization yet. Create one to manage multiple
        companies from a single dashboard.
      </p>
      <router-link to="/org-manage" class="btn btn-primary">
        Create Organization
      </router-link>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="loading" class="loading">Loading dashboard...</div>

    <template v-if="dashboard && !loading">
      <!-- Org Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-label">Companies</div>
          <div class="card-value">
            {{ dashboard.company_count }}
            <span class="card-limit">/ {{ dashboard.organization.max_companies }}</span>
          </div>
        </div>
        <div class="summary-card">
          <div class="card-label">Team Members</div>
          <div class="card-value">
            {{ dashboard.member_count }}
            <span class="card-limit">/ {{ dashboard.organization.max_users }}</span>
          </div>
        </div>
        <div class="summary-card highlight">
          <div class="card-label">Total Revenue (This Month)</div>
          <div class="card-value">{{ fmt(dashboard.total_finance.total_revenue) }}</div>
        </div>
        <div class="summary-card">
          <div class="card-label">Total Net Income</div>
          <div class="card-value">{{ fmt(dashboard.total_finance.total_net_income) }}</div>
        </div>
        <div class="summary-card" :class="{ pass: dashboard.compliance_all_pass, fail: !dashboard.compliance_all_pass }">
          <div class="card-label">CAS Compliance</div>
          <div class="card-value">{{ dashboard.compliance_all_pass ? "ALL PASS" : "ISSUES" }}</div>
        </div>
        <div class="summary-card">
          <div class="card-label">Plan</div>
          <div class="card-value plan-badge">{{ dashboard.organization.plan }}</div>
        </div>
      </div>

      <!-- Company Table -->
      <div class="section">
        <div class="section-header">
          <h2>Companies</h2>
          <button
            class="btn btn-primary"
            :disabled="batchLoading"
            @click="runBatchCompliance"
          >
            {{ batchLoading ? "Running..." : "Batch CAS Check" }}
          </button>
        </div>

        <!-- Batch Results -->
        <div v-if="batchResult" class="batch-results">
          <div class="batch-header" :class="{ pass: batchResult.all_pass, fail: !batchResult.all_pass }">
            Batch Compliance:
            {{ batchResult.all_pass ? "ALL PASSED" : "SOME FAILED" }}
          </div>
          <div class="batch-items">
            <div
              v-for="r in batchResult.results"
              :key="r.company_id"
              class="batch-item"
              :class="{ pass: r.pass, fail: !r.pass }"
            >
              <span class="batch-name">{{ r.company_name }}</span>
              <span class="batch-score">{{ r.score }}%</span>
              <span v-if="r.error" class="batch-error">{{ r.error }}</span>
            </div>
          </div>
        </div>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>TIN</th>
                <th>Jurisdiction</th>
                <th>Reports</th>
                <th>Drafts</th>
                <th>Revenue</th>
                <th>Net Income</th>
                <th>CAS</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in dashboard.companies" :key="c.id">
                <td class="company-name-cell">{{ c.company_name }}</td>
                <td>{{ c.tin_number || "—" }}</td>
                <td>
                  <span class="jurisdiction-tag">{{ c.jurisdiction }}</span>
                </td>
                <td>{{ c.report_count }}</td>
                <td>
                  <span v-if="c.draft_count > 0" class="badge warning">{{ c.draft_count }}</span>
                  <span v-else>0</span>
                </td>
                <td class="money">{{ fmt(c.revenue) }}</td>
                <td class="money" :class="{ positive: parseFloat(c.net_income) > 0, negative: parseFloat(c.net_income) < 0 }">
                  {{ fmt(c.net_income) }}
                </td>
                <td>
                  <span v-if="c.cas_pass === null" class="badge neutral">N/A</span>
                  <span v-else-if="c.cas_pass" class="badge success">PASS</span>
                  <span v-else class="badge danger">FAIL</span>
                </td>
                <td>
                  <button class="btn btn-sm" @click="switchToCompany(c.id)">
                    Open
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.org-dashboard {
  padding: 24px;
  max-width: 1400px;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.view-header h1 {
  font-size: 24px;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.org-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  min-width: 200px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
  padding: 20px;
}

.summary-card.highlight {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: #fff;
  border: none;
}
.summary-card.highlight .card-label { color: rgba(255,255,255,0.8); }
.summary-card.highlight .card-value { color: #fff; }

.summary-card.pass { border-left: 4px solid #10b981; }
.summary-card.fail { border-left: 4px solid #ef4444; }

.card-label {
  font-size: 12px;
  color: var(--text-muted, #6b7280);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
}

.card-limit {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-muted);
}

.plan-badge {
  text-transform: capitalize;
  font-size: 18px;
}

.section {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 18px;
  margin: 0;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border, #e5e7eb);
  font-size: 14px;
}

th {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 12px;
  text-transform: uppercase;
}

.company-name-cell {
  font-weight: 600;
}

.money {
  font-family: 'SF Mono', 'Fira Code', monospace;
  text-align: right;
}

.positive { color: #10b981; }
.negative { color: #ef4444; }

.jurisdiction-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(79, 70, 229, 0.1);
  color: #4f46e5;
  font-weight: 600;
}

.badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.badge.success { background: #d1fae5; color: #065f46; }
.badge.danger { background: #fee2e2; color: #991b1b; }
.badge.warning { background: #fef3c7; color: #92400e; }
.badge.neutral { background: #f3f4f6; color: #6b7280; }

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}
.btn-primary {
  background: #4f46e5;
  color: #fff;
}
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border, #e5e7eb);
  color: var(--text, #1f2937);
}
.btn-outline:hover { background: var(--bg-hover, #f9fafb); }
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  background: #f3f4f6;
  border: 1px solid var(--border, #e5e7eb);
}
.btn-sm:hover { background: #e5e7eb; }

.batch-results {
  margin-bottom: 16px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 8px;
  overflow: hidden;
}
.batch-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
}
.batch-header.pass { background: #d1fae5; color: #065f46; }
.batch-header.fail { background: #fee2e2; color: #991b1b; }
.batch-items { padding: 8px 16px; }
.batch-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border, #e5e7eb);
  font-size: 13px;
}
.batch-item:last-child { border-bottom: none; }
.batch-item.pass .batch-score { color: #10b981; }
.batch-item.fail .batch-score { color: #ef4444; }
.batch-name { flex: 1; }
.batch-score { font-weight: 700; }
.batch-error { color: #ef4444; font-size: 12px; }

.empty-state {
  text-align: center;
  padding: 60px 24px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
}
.empty-state h3 { font-size: 20px; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 24px; }

.error-banner {
  background: #fee2e2;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .org-dashboard {
    padding: 12px;
    max-width: none;
  }
  .view-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
  .org-select {
    width: 100%;
  }
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .section {
    padding: 16px;
  }
  table {
    min-width: 700px;
  }
}
</style>
</template>
