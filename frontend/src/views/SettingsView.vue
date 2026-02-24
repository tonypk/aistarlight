<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { client } from '../api/client'
import { authApi } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

// Company settings
const form = ref({
  company_name: '',
  tin_number: '',
  rdo_code: '',
  vat_classification: 'vat_registered',
})
const saving = ref(false)
const saved = ref(false)
const apiKey = ref('')

// Team management
interface TeamMember {
  id: string
  email: string
  full_name: string
  role: string
  created_at: string | null
}
const teamMembers = ref<TeamMember[]>([])
const teamLoading = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('viewer')
const inviting = ref(false)
const inviteMsg = ref('')
const inviteErr = ref('')

const isOwnerOrAdmin = computed(() => ['owner', 'admin'].includes(auth.currentRole))

onMounted(async () => {
  const res = await client.get('/settings/company')
  const data = res.data.data
  form.value = {
    company_name: data.company_name || '',
    tin_number: data.tin_number || '',
    rdo_code: data.rdo_code || '',
    vat_classification: data.vat_classification || 'vat_registered',
  }
  await fetchTeam()
})

async function fetchTeam() {
  teamLoading.value = true
  try {
    const res = await client.get('/settings/team')
    teamMembers.value = res.data.data || []
  } finally {
    teamLoading.value = false
  }
}

async function handleSave() {
  saving.value = true
  saved.value = false
  try {
    await client.put('/settings/company', form.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

async function generateApiKey() {
  if (!confirm('Generate a new API key? This will invalidate any existing key.')) return
  const res = await client.post('/auth/api-key')
  apiKey.value = res.data.data.api_key
}

async function handleInvite() {
  if (!inviteEmail.value) return
  inviting.value = true
  inviteMsg.value = ''
  inviteErr.value = ''
  try {
    await authApi.inviteMember(inviteEmail.value, inviteRole.value)
    inviteMsg.value = `Invited ${inviteEmail.value} as ${inviteRole.value}`
    inviteEmail.value = ''
    inviteRole.value = 'viewer'
    await fetchTeam()
    setTimeout(() => { inviteMsg.value = '' }, 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    inviteErr.value = err.response?.data?.error || 'Failed to invite member'
  } finally {
    inviting.value = false
  }
}

async function handleRoleChange(member: TeamMember, newRole: string) {
  try {
    await client.patch(`/settings/team/${member.id}/role?role=${newRole}`)
    member.role = newRole
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    alert(err.response?.data?.error || 'Failed to update role')
    await fetchTeam()
  }
}
</script>

<template>
  <div class="settings-view">
    <h2>Settings</h2>

    <!-- Company Settings -->
    <div class="section-card">
      <h3>Company Information</h3>
      <form class="settings-form" @submit.prevent="handleSave">
        <div class="field">
          <label>Company Name</label>
          <input v-model="form.company_name" required />
        </div>
        <div class="field">
          <label>TIN (Tax Identification Number)</label>
          <input v-model="form.tin_number" placeholder="123-456-789-000" />
        </div>
        <div class="field">
          <label>RDO Code</label>
          <input v-model="form.rdo_code" placeholder="e.g., 050" />
        </div>
        <div class="field">
          <label>VAT Classification</label>
          <select v-model="form.vat_classification">
            <option value="vat_registered">VAT Registered</option>
            <option value="non_vat">Non-VAT (Percentage Tax)</option>
          </select>
        </div>
        <button type="submit" :disabled="saving" class="primary-btn">
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
        <span v-if="saved" class="success-msg">Settings saved!</span>
      </form>
    </div>

    <!-- Team Management -->
    <div class="section-card">
      <h3>Team Members</h3>

      <!-- Invite Form (admin/owner only) -->
      <div v-if="isOwnerOrAdmin" class="invite-form">
        <div class="invite-row">
          <input
            v-model="inviteEmail"
            type="email"
            placeholder="Email address"
            class="invite-input"
          />
          <select v-model="inviteRole" class="invite-select">
            <option value="viewer">Viewer</option>
            <option value="accountant">Accountant</option>
            <option value="admin">Admin</option>
          </select>
          <button
            class="primary-btn"
            :disabled="inviting || !inviteEmail"
            @click="handleInvite"
          >
            {{ inviting ? 'Inviting...' : 'Invite' }}
          </button>
        </div>
        <p v-if="inviteMsg" class="success-msg">{{ inviteMsg }}</p>
        <p v-if="inviteErr" class="error-msg">{{ inviteErr }}</p>
      </div>

      <!-- Members Table -->
      <div v-if="teamLoading" class="loading">Loading team...</div>
      <table v-else-if="teamMembers.length" class="team-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Joined</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in teamMembers" :key="m.id">
            <td>{{ m.full_name || '—' }}</td>
            <td>{{ m.email }}</td>
            <td>
              <select
                v-if="isOwnerOrAdmin && m.role !== 'owner' && m.id !== auth.user?.id"
                :value="m.role"
                @change="handleRoleChange(m, ($event.target as HTMLSelectElement).value)"
                class="role-select"
              >
                <option value="viewer">Viewer</option>
                <option value="accountant">Accountant</option>
                <option value="admin">Admin</option>
              </select>
              <span v-else class="role-badge" :class="m.role">{{ m.role }}</span>
            </td>
            <td>{{ m.created_at ? new Date(m.created_at).toLocaleDateString() : '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">No team members found.</p>
    </div>

    <!-- API Access -->
    <div class="section-card">
      <h3>API Access</h3>
      <p class="desc">Generate an API key for programmatic access to the AIStarlight API.</p>
      <button class="api-btn" @click="generateApiKey">Generate API Key</button>
      <div v-if="apiKey" class="api-key">
        <code>{{ apiKey }}</code>
        <p class="warn">Save this key - it won't be shown again!</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-view h2 { margin-bottom: 24px; }

.section-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  max-width: 700px;
  margin-bottom: 24px;
}
.section-card h3 {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

.settings-form { max-width: 500px; }
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 4px; font-size: 14px; color: #555; }
.field input, .field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

.primary-btn {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.primary-btn:hover { background: #4338ca; }
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.success-msg { color: #059669; margin-left: 12px; font-size: 14px; }
.error-msg { color: #ef4444; font-size: 14px; margin-top: 8px; }

/* Invite */
.invite-form { margin-bottom: 20px; }
.invite-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.invite-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}
.invite-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}

/* Team table */
.team-table {
  width: 100%;
  border-collapse: collapse;
}
.team-table th {
  text-align: left;
  padding: 8px;
  color: #888;
  font-size: 13px;
  border-bottom: 1px solid #e5e7eb;
}
.team-table td {
  padding: 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
}
.role-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
}
.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.role-badge.owner { background: #fef3c7; color: #92400e; }
.role-badge.admin { background: #dbeafe; color: #1e40af; }
.role-badge.accountant { background: #d1fae5; color: #065f46; }
.role-badge.viewer { background: #f3f4f6; color: #6b7280; }

.loading { color: #888; padding: 20px 0; }
.empty { color: #888; font-size: 14px; }
.desc { color: #888; margin-bottom: 16px; font-size: 14px; }

/* API */
.api-btn {
  padding: 10px 24px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.api-btn:hover { background: #047857; }
.api-key {
  margin-top: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}
.api-key code {
  display: block;
  font-size: 14px;
  word-break: break-all;
  color: #1a1a2e;
}
.warn { color: #ef4444; font-size: 12px; margin-top: 8px; }
</style>
