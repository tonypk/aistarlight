<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { client } from '../api/client'
import { authApi, type CreateMemberData } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'

const auth = useAuthStore()
const ui = useUIStore()

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
  telegram_username: string | null
  telegram_linked: boolean
}
const teamMembers = ref<TeamMember[]>([])
const teamLoading = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('viewer')
const inviting = ref(false)
const inviteMsg = ref('')
const inviteErr = ref('')

// Create Member
const showCreateMember = ref(false)
const createForm = ref<CreateMemberData>({
  email: '',
  password: '',
  full_name: '',
  telegram_username: '',
  role: 'member',
})
const autoPassword = ref(true)
const creating = ref(false)
const createResult = ref<{
  email: string
  password: string
  api_key: string
  deep_link?: string
} | null>(null)
const createErr = ref('')

// Telegram binding (current user)
const tgStatus = ref<{
  linked: boolean
  username?: string
  bot_name?: string
  linked_at?: string
} | null>(null)
const tgLoading = ref(false)
const tgLink = ref('')
const tgLinkLoading = ref(false)

const isOwnerOrAdmin = computed(() => ['owner', 'admin', 'company_admin'].includes(auth.currentRole))

function generatePassword(length = 12): string {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$'
  const array = new Uint8Array(length)
  crypto.getRandomValues(array)
  return Array.from(array, (b) => chars[b % chars.length]).join('')
}

onMounted(async () => {
  const res = await client.get('/settings/company')
  const data = res.data.data
  form.value = {
    company_name: data.company_name || '',
    tin_number: data.tin_number || '',
    rdo_code: data.rdo_code || '',
    vat_classification: data.vat_classification || 'vat_registered',
  }
  await Promise.all([fetchTeam(), fetchTelegramStatus()])
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

async function fetchTelegramStatus() {
  tgLoading.value = true
  try {
    const res = await authApi.getTelegramStatus()
    tgStatus.value = res.data.data
  } catch {
    tgStatus.value = null
  } finally {
    tgLoading.value = false
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

async function handleCreateMember() {
  creating.value = true
  createErr.value = ''
  createResult.value = null
  try {
    const password = autoPassword.value ? generatePassword() : createForm.value.password
    const data: CreateMemberData = {
      email: createForm.value.email,
      password,
      full_name: createForm.value.full_name,
      role: createForm.value.role || 'member',
    }
    if (createForm.value.telegram_username) {
      data.telegram_username = createForm.value.telegram_username
    }
    const res = await authApi.createMember(data)
    const result = res.data.data
    createResult.value = {
      email: data.email,
      password,
      api_key: result.api_key,
      deep_link: result.deep_link,
    }
    // Reset form
    createForm.value = { email: '', password: '', full_name: '', telegram_username: '', role: 'member' }
    await fetchTeam()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { error?: string } } }
    createErr.value = err.response?.data?.error || 'Failed to create member'
  } finally {
    creating.value = false
  }
}

async function copyCreateResult() {
  if (!createResult.value) return
  const lines = [
    `Email: ${createResult.value.email}`,
    `Password: ${createResult.value.password}`,
    `API Key: ${createResult.value.api_key}`,
  ]
  if (createResult.value.deep_link) {
    lines.push(`Telegram Link: ${createResult.value.deep_link}`)
  }
  await navigator.clipboard.writeText(lines.join('\n'))
}

async function handleConnectTelegram() {
  tgLinkLoading.value = true
  try {
    const res = await authApi.generateTelegramLink()
    tgLink.value = res.data.data.deep_link
  } catch {
    tgLink.value = ''
  } finally {
    tgLinkLoading.value = false
  }
}

async function copyTelegramLink() {
  if (tgLink.value) {
    await navigator.clipboard.writeText(tgLink.value)
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

    <!-- Appearance -->
    <div class="section-card">
      <h3>Appearance</h3>
      <div class="appearance-row">
        <div class="appearance-info">
          <strong>Dark Mode</strong>
          <p class="desc">Switch between light and dark themes</p>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" :checked="ui.isDarkMode" @change="ui.toggleDarkMode()" />
          <span class="toggle-slider"></span>
        </label>
      </div>
    </div>

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

    <!-- Telegram Bot Binding (all users) -->
    <div class="section-card">
      <h3>Telegram Bot</h3>
      <div v-if="tgLoading" class="loading">Loading...</div>
      <template v-else-if="tgStatus">
        <div v-if="tgStatus.linked" class="tg-status tg-linked">
          <span class="status-dot green"></span>
          <span>Connected as <strong>@{{ tgStatus.username }}</strong></span>
          <span v-if="tgStatus.linked_at" class="tg-date">
            since {{ new Date(tgStatus.linked_at).toLocaleDateString() }}
          </span>
        </div>
        <div v-else class="tg-status tg-unlinked">
          <span class="status-dot gray"></span>
          <span>Not connected</span>
          <button
            class="primary-btn tg-btn"
            :disabled="tgLinkLoading"
            @click="handleConnectTelegram"
          >
            {{ tgLinkLoading ? 'Generating...' : 'Connect Telegram' }}
          </button>
        </div>
        <div v-if="tgLink" class="tg-link-box">
          <p>Open this link to connect your Telegram account:</p>
          <div class="tg-link-row">
            <a :href="tgLink" target="_blank" class="tg-deep-link">{{ tgLink }}</a>
            <button class="copy-btn" @click="copyTelegramLink" title="Copy link">Copy</button>
          </div>
        </div>
      </template>
    </div>

    <!-- Team Management -->
    <div class="section-card">
      <h3>Team Members</h3>

      <!-- Create Member Form (admin-only) -->
      <div v-if="isOwnerOrAdmin" class="create-member-section">
        <button
          class="secondary-btn"
          @click="showCreateMember = !showCreateMember"
        >
          {{ showCreateMember ? 'Cancel' : '+ Create Member' }}
        </button>

        <div v-if="showCreateMember" class="create-form">
          <div class="field">
            <label>Full Name</label>
            <input v-model="createForm.full_name" required placeholder="John Doe" />
          </div>
          <div class="field">
            <label>Email</label>
            <input v-model="createForm.email" type="email" required placeholder="user@example.com" />
          </div>
          <div class="field">
            <label>
              <input type="checkbox" v-model="autoPassword" /> Auto-generate password
            </label>
            <input
              v-if="!autoPassword"
              v-model="createForm.password"
              type="text"
              placeholder="Min 8 characters"
              minlength="8"
            />
          </div>
          <div class="field">
            <label>Telegram Username (optional)</label>
            <input v-model="createForm.telegram_username" placeholder="@username" />
          </div>
          <div class="field">
            <label>Role</label>
            <select v-model="createForm.role">
              <option value="member">Member</option>
              <option value="accountant">Accountant</option>
              <option value="viewer">Viewer</option>
              <option value="company_admin">Admin</option>
            </select>
          </div>
          <button
            class="primary-btn"
            :disabled="creating || !createForm.email || !createForm.full_name"
            @click="handleCreateMember"
          >
            {{ creating ? 'Creating...' : 'Create Member' }}
          </button>
          <p v-if="createErr" class="error-msg">{{ createErr }}</p>
        </div>

        <!-- Result Card -->
        <div v-if="createResult" class="result-card">
          <h4>Member Created Successfully</h4>
          <div class="result-row"><span class="result-label">Email:</span> {{ createResult.email }}</div>
          <div class="result-row"><span class="result-label">Password:</span> <code>{{ createResult.password }}</code></div>
          <div class="result-row"><span class="result-label">API Key:</span> <code class="api-code">{{ createResult.api_key }}</code></div>
          <div v-if="createResult.deep_link" class="result-row">
            <span class="result-label">Telegram:</span>
            <a :href="createResult.deep_link" target="_blank" class="tg-deep-link">{{ createResult.deep_link }}</a>
          </div>
          <div class="result-actions">
            <button class="primary-btn" @click="copyCreateResult">Copy All</button>
            <button class="secondary-btn" @click="createResult = null">Dismiss</button>
          </div>
          <p class="warn">Save these credentials - they won't be shown again!</p>
        </div>
      </div>

      <!-- Invite Form (admin/owner only) -->
      <div v-if="isOwnerOrAdmin" class="invite-form">
        <p class="desc">Or invite an existing user by email:</p>
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
            <th>Telegram</th>
            <th>Joined</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in teamMembers" :key="m.id">
            <td>{{ m.full_name || '\u2014' }}</td>
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
                <option value="member">Member</option>
                <option value="company_admin">Admin</option>
              </select>
              <span v-else class="role-badge" :class="m.role">{{ m.role }}</span>
            </td>
            <td>
              <span v-if="m.telegram_linked" class="tg-cell">
                <span class="status-dot green"></span>
                {{ m.telegram_username ? '@' + m.telegram_username : 'Linked' }}
              </span>
              <span v-else class="tg-cell">
                <span class="status-dot gray"></span>
                <span class="muted">Not linked</span>
              </span>
            </td>
            <td>{{ m.created_at ? new Date(m.created_at).toLocaleDateString() : '\u2014' }}</td>
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
.settings-view h2 { margin-bottom: 24px; color: var(--text-primary); }

.section-card {
  background: var(--bg-surface);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border-default);
  max-width: 800px;
  margin-bottom: 24px;
}
.section-card h3 {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
  color: var(--text-primary);
}

/* Appearance toggle */
.appearance-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.appearance-info strong { color: var(--text-primary); }
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
  cursor: pointer;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute;
  inset: 0;
  background: #d1d5db;
  border-radius: 26px;
  transition: background 0.2s;
}
.toggle-slider::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-switch input:checked + .toggle-slider {
  background: var(--brand-primary);
}
.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(22px);
}

.settings-form { max-width: 500px; }
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 4px; font-size: 14px; color: var(--text-secondary); }
.field input[type="text"],
.field input[type="email"],
.field input:not([type]),
.field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-input);
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  background: var(--bg-input);
  color: var(--text-primary);
}

.primary-btn {
  padding: 10px 24px;
  background: var(--brand-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.primary-btn:hover { background: var(--brand-primary-hover); }
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.secondary-btn {
  padding: 10px 24px;
  background: var(--bg-surface-alt);
  color: var(--text-primary);
  border: 1px solid var(--border-input);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.secondary-btn:hover { background: var(--bg-surface-hover); }

.success-msg { color: #059669; margin-left: 12px; font-size: 14px; }
.error-msg { color: #ef4444; font-size: 14px; margin-top: 8px; }

/* Create Member */
.create-member-section { margin-bottom: 20px; }
.create-form {
  margin-top: 16px;
  padding: 20px;
  background: var(--bg-surface-alt);
  border-radius: 8px;
  max-width: 500px;
}

.result-card {
  margin-top: 16px;
  padding: 20px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  max-width: 500px;
}
html.dark .result-card { background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); }
.result-card h4 { margin: 0 0 12px; color: #065f46; }
html.dark .result-card h4 { color: #6ee7b7; }
.result-row {
  margin-bottom: 8px;
  font-size: 14px;
  word-break: break-all;
  color: var(--text-primary);
}
.result-label { font-weight: 600; margin-right: 4px; }
.result-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.api-code { font-size: 12px; }

/* Telegram */
.tg-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
}
.tg-btn { margin-left: auto; }
.tg-date { color: var(--text-secondary); font-size: 13px; }
.tg-link-box {
  margin-top: 12px;
  padding: 12px;
  background: #f0fdf4;
  border-radius: 8px;
}
html.dark .tg-link-box { background: rgba(16,185,129,0.1); }
.tg-link-box p { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.tg-link-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.tg-deep-link {
  color: var(--brand-primary);
  font-size: 13px;
  word-break: break-all;
}
.copy-btn {
  padding: 4px 12px;
  background: var(--bg-surface-hover);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  color: var(--text-primary);
}
.copy-btn:hover { background: var(--border-default); }

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.green { background: #10b981; }
.status-dot.gray { background: #9ca3af; }

.tg-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.muted { color: var(--text-muted); }

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
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
}
.invite-select {
  padding: 8px 12px;
  border: 1px solid var(--border-input);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
}

/* Team table */
.team-table {
  width: 100%;
  border-collapse: collapse;
}
.team-table th {
  text-align: left;
  padding: 8px;
  color: var(--text-muted);
  font-size: 13px;
  border-bottom: 1px solid var(--border-default);
}
.team-table td {
  padding: 8px;
  border-bottom: 1px solid var(--bg-surface-alt);
  font-size: 14px;
  color: var(--text-primary);
}
.role-select {
  padding: 4px 8px;
  border: 1px solid var(--border-input);
  border-radius: 4px;
  font-size: 13px;
  background: var(--bg-input);
  color: var(--text-primary);
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
.role-badge.admin, .role-badge.company_admin { background: #dbeafe; color: #1e40af; }
.role-badge.accountant { background: #d1fae5; color: #065f46; }
.role-badge.viewer { background: var(--bg-surface-alt); color: var(--text-secondary); }
.role-badge.member { background: #e0e7ff; color: #3730a3; }

.loading { color: var(--text-muted); padding: 20px 0; }
.empty { color: var(--text-muted); font-size: 14px; }
.desc { color: var(--text-muted); margin-bottom: 12px; font-size: 14px; }

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
  background: var(--bg-surface-alt);
  border-radius: 8px;
}
.api-key code {
  display: block;
  font-size: 14px;
  word-break: break-all;
  color: var(--text-primary);
}
.warn { color: #ef4444; font-size: 12px; margin-top: 8px; }
</style>
