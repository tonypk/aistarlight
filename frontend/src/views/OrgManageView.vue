<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import {
  orgApi,
  type Organization,
  type OrgMember,
} from "../api/org";

const orgs = ref<Organization[]>([]);
const selectedOrgId = ref("");
const selectedOrg = computed(() => orgs.value.find((o) => o.id === selectedOrgId.value));
const members = ref<OrgMember[]>([]);
const loading = ref(false);
const error = ref("");
const successMsg = ref("");

// Create org form
const showCreateForm = ref(false);
const newOrgName = ref("");
const creating = ref(false);

// Add member form
const showAddMember = ref(false);
const newMemberEmail = ref("");
const newMemberRole = ref("org_member");
const addingMember = ref(false);

const tab = ref<"members" | "settings">("members");

async function loadOrgs() {
  loading.value = true;
  try {
    const res = await orgApi.list();
    orgs.value = res.data.data || [];
    if (orgs.value.length > 0 && !selectedOrgId.value) {
      selectedOrgId.value = orgs.value[0].id;
      await loadMembers();
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load";
  } finally {
    loading.value = false;
  }
}

async function loadMembers() {
  if (!selectedOrgId.value) return;
  try {
    const res = await orgApi.listMembers(selectedOrgId.value);
    members.value = res.data.data || [];
  } catch {
    members.value = [];
  }
}

async function createOrg() {
  if (!newOrgName.value.trim()) return;
  creating.value = true;
  error.value = "";
  try {
    await orgApi.create({ name: newOrgName.value.trim() });
    newOrgName.value = "";
    showCreateForm.value = false;
    successMsg.value = "Organization created!";
    await loadOrgs();
    setTimeout(() => (successMsg.value = ""), 3000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to create";
  } finally {
    creating.value = false;
  }
}

async function updateOrgSettings() {
  if (!selectedOrg.value) return;
  error.value = "";
  try {
    await orgApi.update(selectedOrg.value.id, {
      name: selectedOrg.value.name,
      slug: selectedOrg.value.slug,
    });
    successMsg.value = "Settings saved!";
    await loadOrgs();
    setTimeout(() => (successMsg.value = ""), 3000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to update";
  }
}

async function addMember() {
  if (!newMemberEmail.value.trim() || !selectedOrgId.value) return;
  addingMember.value = true;
  error.value = "";
  try {
    // The API expects user_id, but for convenience we pass email
    // Backend should resolve — if not, we need to extend the API
    await orgApi.addMember(selectedOrgId.value, newMemberEmail.value.trim(), newMemberRole.value);
    newMemberEmail.value = "";
    showAddMember.value = false;
    successMsg.value = "Member added!";
    await loadMembers();
    setTimeout(() => (successMsg.value = ""), 3000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to add member";
  } finally {
    addingMember.value = false;
  }
}

async function updateRole(userId: string, role: string) {
  if (!selectedOrgId.value) return;
  try {
    await orgApi.updateMemberRole(selectedOrgId.value, userId, role);
    successMsg.value = "Role updated!";
    await loadMembers();
    setTimeout(() => (successMsg.value = ""), 3000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to update role";
  }
}

async function removeMember(userId: string, name: string) {
  if (!confirm(`Remove ${name} from this organization?`)) return;
  try {
    await orgApi.removeMember(selectedOrgId.value, userId);
    successMsg.value = "Member removed";
    await loadMembers();
    setTimeout(() => (successMsg.value = ""), 3000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to remove";
  }
}

function roleLabel(role: string): string {
  const labels: Record<string, string> = {
    org_owner: "Owner",
    org_admin: "Admin",
    org_member: "Member",
  };
  return labels[role] || role;
}

function roleBadgeClass(role: string): string {
  if (role === "org_owner") return "badge owner";
  if (role === "org_admin") return "badge admin";
  return "badge member";
}

onMounted(loadOrgs);
</script>

<template>
  <div class="org-manage">
    <div class="view-header">
      <h1>Organization Management</h1>
      <div class="header-actions">
        <select
          v-if="orgs.length > 1"
          v-model="selectedOrgId"
          @change="loadMembers"
          class="org-select"
        >
          <option v-for="org in orgs" :key="org.id" :value="org.id">
            {{ org.name }}
          </option>
        </select>
        <button class="btn btn-primary" @click="showCreateForm = true">
          + New Organization
        </button>
      </div>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="successMsg" class="success-banner">{{ successMsg }}</div>

    <!-- Create Org Modal -->
    <div v-if="showCreateForm" class="modal-overlay" @click.self="showCreateForm = false">
      <div class="modal-content">
        <h3>Create Organization</h3>
        <div class="form-group">
          <label>Organization Name</label>
          <input
            v-model="newOrgName"
            type="text"
            placeholder="e.g. Acme Accounting Firm"
            @keyup.enter="createOrg"
          />
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showCreateForm = false">Cancel</button>
          <button class="btn btn-primary" :disabled="creating || !newOrgName.trim()" @click="createOrg">
            {{ creating ? "Creating..." : "Create" }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <template v-if="selectedOrg && !loading">
      <!-- Org Info Card -->
      <div class="org-info-card">
        <div class="org-info-row">
          <div>
            <h2>{{ selectedOrg.name }}</h2>
            <span class="slug">{{ selectedOrg.slug }}</span>
          </div>
          <div class="org-meta">
            <span class="plan-badge">{{ selectedOrg.plan }}</span>
            <span class="limit-info">
              {{ selectedOrg.max_companies }} companies / {{ selectedOrg.max_users }} users
            </span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="{ active: tab === 'members' }" @click="tab = 'members'">
          Members ({{ members.length }})
        </button>
        <button :class="{ active: tab === 'settings' }" @click="tab = 'settings'">
          Settings
        </button>
      </div>

      <!-- Members Tab -->
      <div v-if="tab === 'members'" class="tab-content">
        <div class="section-header">
          <h3>Team Members</h3>
          <button class="btn btn-primary btn-sm" @click="showAddMember = true">
            + Add Member
          </button>
        </div>

        <!-- Add Member Form -->
        <div v-if="showAddMember" class="inline-form">
          <input
            v-model="newMemberEmail"
            type="text"
            placeholder="User ID (UUID)"
            class="form-input"
          />
          <select v-model="newMemberRole" class="form-select">
            <option value="org_member">Member</option>
            <option value="org_admin">Admin</option>
          </select>
          <button class="btn btn-primary btn-sm" :disabled="addingMember" @click="addMember">
            {{ addingMember ? "Adding..." : "Add" }}
          </button>
          <button class="btn btn-outline btn-sm" @click="showAddMember = false">Cancel</button>
        </div>

        <div class="members-list">
          <div v-for="m in members" :key="m.user_id" class="member-card">
            <div class="member-info">
              <div class="member-avatar">
                {{ (m.full_name || m.email || "?")[0].toUpperCase() }}
              </div>
              <div>
                <div class="member-name">{{ m.full_name || m.email }}</div>
                <div class="member-email">{{ m.email }}</div>
              </div>
            </div>
            <div class="member-actions">
              <span :class="roleBadgeClass(m.role)">{{ roleLabel(m.role) }}</span>
              <select
                v-if="m.role !== 'org_owner'"
                :value="m.role"
                @change="updateRole(m.user_id, ($event.target as HTMLSelectElement).value)"
                class="role-select"
              >
                <option value="org_member">Member</option>
                <option value="org_admin">Admin</option>
              </select>
              <button
                v-if="m.role !== 'org_owner'"
                class="btn-icon danger"
                @click="removeMember(m.user_id, m.full_name || m.email)"
                title="Remove member"
              >
                &times;
              </button>
            </div>
          </div>
          <div v-if="members.length === 0" class="empty">No members found</div>
        </div>
      </div>

      <!-- Settings Tab -->
      <div v-if="tab === 'settings'" class="tab-content">
        <div class="settings-form">
          <div class="form-group">
            <label>Organization Name</label>
            <input v-model="selectedOrg.name" type="text" />
          </div>
          <div class="form-group">
            <label>Slug (URL-friendly identifier)</label>
            <input v-model="selectedOrg.slug" type="text" />
          </div>
          <div class="form-group">
            <label>Plan</label>
            <input :value="selectedOrg.plan" type="text" disabled />
            <small>Contact support to change your plan</small>
          </div>
          <button class="btn btn-primary" @click="updateOrgSettings">
            Save Settings
          </button>
        </div>
      </div>
    </template>

    <div v-if="!selectedOrg && !loading && orgs.length === 0" class="empty-state">
      <h3>No Organizations</h3>
      <p>Create an organization to manage multiple companies and team members.</p>
      <button class="btn btn-primary" @click="showCreateForm = true">
        Create Your First Organization
      </button>
    </div>
  </div>
</template>

<style scoped>
.org-manage {
  padding: 24px;
  max-width: 1000px;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.view-header h1 { font-size: 24px; margin: 0; }

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

.org-info-card {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}

.org-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.org-info-row h2 { margin: 0; font-size: 20px; }
.slug { font-size: 13px; color: var(--text-muted); }

.org-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.plan-badge {
  padding: 4px 12px;
  border-radius: 6px;
  background: rgba(79, 70, 229, 0.1);
  color: #4f46e5;
  font-weight: 600;
  font-size: 13px;
  text-transform: capitalize;
}

.limit-info {
  font-size: 13px;
  color: var(--text-muted);
}

.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--border, #e5e7eb);
  margin-bottom: 0;
}

.tabs button {
  padding: 12px 24px;
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tabs button.active {
  color: #4f46e5;
  border-bottom-color: #4f46e5;
}

.tab-content {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-top: none;
  border-radius: 0 0 10px 10px;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 { margin: 0; font-size: 16px; }

.inline-form {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 12px;
  background: var(--bg-hover, #f9fafb);
  border-radius: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.form-input, .form-select {
  padding: 8px 12px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 6px;
  font-size: 14px;
}

.form-input { flex: 1; min-width: 180px; }

.members-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #4f46e5;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.member-name { font-weight: 600; font-size: 14px; }
.member-email { font-size: 12px; color: var(--text-muted); }

.member-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.badge {
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.badge.owner { background: #fef3c7; color: #92400e; }
.badge.admin { background: #dbeafe; color: #1e40af; }
.badge.member { background: #f3f4f6; color: #6b7280; }

.role-select {
  padding: 4px 8px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 4px;
  font-size: 12px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-icon.danger:hover { background: #fee2e2; color: #dc2626; }

.settings-form {
  max-width: 500px;
}

.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}
.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 6px;
  font-size: 14px;
}
.form-group input:disabled {
  background: var(--bg-hover, #f9fafb);
  color: var(--text-muted);
}
.form-group small {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

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
.btn-primary { background: #4f46e5; color: #fff; }
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline {
  background: transparent;
  border: 1px solid var(--border, #e5e7eb);
  color: var(--text, #1f2937);
}
.btn-outline:hover { background: var(--bg-hover, #f9fafb); }
.btn-sm { padding: 6px 12px; font-size: 12px; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card, #fff);
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 450px;
}

.modal-content h3 { margin: 0 0 16px; font-size: 18px; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.error-banner {
  background: #fee2e2;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.success-banner {
  background: #d1fae5;
  color: #065f46;
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

.empty-state {
  text-align: center;
  padding: 60px 24px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 10px;
}
.empty-state h3 { font-size: 20px; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 24px; }

.empty {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 14px;
}

@media (max-width: 768px) {
  .org-manage {
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
  .org-select { width: 100%; }
  .org-info-row { flex-direction: column; align-items: flex-start; }
  .tab-content { padding: 16px; }
  .member-card { flex-direction: column; align-items: flex-start; }
  .member-actions { width: 100%; justify-content: flex-end; }
  .inline-form { flex-direction: column; }
  .form-input { width: 100%; }
}
</style>
