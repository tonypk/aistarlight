<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Role-based menu: minRole defines minimum access level
const menuItems = [
  { name: 'Dashboard', path: '/', icon: '📊', minRole: 'viewer' },
  { name: 'Upload Data', path: '/upload', icon: '📤', minRole: 'accountant' },
  { name: 'Receipt Scanner', path: '/receipts', icon: '🧾', minRole: 'accountant' },
  { name: 'Classification', path: '/classification', icon: '🏷️', minRole: 'accountant' },
  { name: 'Reconciliation', path: '/reconciliation', icon: '🔍', minRole: 'accountant' },
  { name: 'Bank Recon', path: '/bank-reconciliation', icon: '🏦', minRole: 'accountant' },
  { name: 'Reports', path: '/reports', icon: '📋', minRole: 'viewer' },
  { name: 'Filing Calendar', path: '/calendar', icon: '📅', minRole: 'viewer' },
  { name: 'Period Compare', path: '/compare', icon: '⚖️', minRole: 'viewer' },
  { name: 'Suppliers', path: '/suppliers', icon: '🏢', minRole: 'accountant' },
  { name: 'Withholding Tax', path: '/withholding', icon: '📑', minRole: 'accountant' },
  { name: 'divider', path: '', icon: '', minRole: 'accountant', divider: true, label: 'Accounting' },
  { name: 'Chart of Accounts', path: '/accounts', icon: '📒', minRole: 'accountant' },
  { name: 'Journal Entries', path: '/journal-entries', icon: '📝', minRole: 'accountant' },
  { name: 'General Ledger', path: '/general-ledger', icon: '📓', minRole: 'accountant' },
  { name: 'Financial Statements', path: '/statements', icon: '📊', minRole: 'accountant' },
  { name: 'Tax from GL', path: '/tax-bridge', icon: '🧮', minRole: 'accountant' },
  { name: 'Learning Insights', path: '/learning', icon: '🎓', minRole: 'viewer' },
  { name: 'AI Chat', path: '/chat', icon: '💬', minRole: 'viewer' },
  { name: 'Knowledge', path: '/knowledge', icon: '📚', minRole: 'viewer' },
  { name: 'Memory', path: '/memory', icon: '🧠', minRole: 'admin' },
  { name: 'User Guide', path: '/guide', icon: '📖', minRole: 'viewer' },
  { name: 'Settings', path: '/settings', icon: '⚙️', minRole: 'admin' },
]

const ROLE_LEVEL: Record<string, number> = {
  viewer: 1,
  accountant: 2,
  admin: 3,
  company_admin: 3,
  owner: 4,
}

const visibleMenuItems = computed(() => {
  const userLevel = ROLE_LEVEL[auth.currentRole] || 1
  return menuItems.filter(item => userLevel >= (ROLE_LEVEL[item.minRole] || 1))
})

onMounted(() => {
  auth.fetchCompanies()
})

async function handleSwitchCompany(event: Event) {
  const target = event.target as HTMLSelectElement
  const tenantId = target.value
  if (tenantId && tenantId !== auth.user?.tenant_id) {
    await auth.switchCompany(tenantId)
    router.push('/')
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <h2>AIStarlight</h2>
      <p class="tagline">Tax Filing Assistant</p>
    </div>

    <!-- Company Switcher -->
    <div v-if="auth.companies.length > 1" class="company-switcher">
      <select :value="auth.user?.tenant_id" @change="handleSwitchCompany">
        <option
          v-for="c in auth.companies"
          :key="c.tenant_id"
          :value="c.tenant_id"
        >{{ c.company_name }}</option>
      </select>
    </div>
    <div v-else-if="auth.user" class="company-name">
      {{ auth.user.company_name }}
    </div>

    <nav>
      <template v-for="item in visibleMenuItems" :key="item.path || item.label">
        <div v-if="item.divider" class="nav-divider">{{ item.label }}</div>
        <router-link
          v-else
          :to="item.path"
          class="nav-item"
          active-class="active"
          :data-testid="`sidebar-nav-${item.path.replace('/', '') || 'dashboard'}`"
        >
          <span class="icon">{{ item.icon }}</span>
          {{ item.name }}
        </router-link>
      </template>
    </nav>

    <div class="sidebar-footer">
      <div v-if="auth.user" class="user-info">
        <span class="user-name">{{ auth.user.full_name || auth.user.email }}</span>
        <span class="user-role">{{ auth.currentRole }}</span>
      </div>
      <button class="logout-btn" @click="handleLogout" data-testid="sidebar-logout">Logout</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}
.logo {
  padding: 24px 20px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo h2 { font-size: 20px; margin: 0; }
.tagline { font-size: 12px; color: #888; margin-top: 4px; }

.company-switcher {
  padding: 8px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.company-switcher select {
  width: 100%;
  padding: 6px 8px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: #fff;
  border-radius: 4px;
  font-size: 13px;
}
.company-switcher select option {
  background: #1a1a2e;
  color: #fff;
}
.company-name {
  padding: 8px 20px;
  font-size: 13px;
  color: #94a3b8;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

nav {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}
nav::-webkit-scrollbar { width: 4px; }
nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
nav::-webkit-scrollbar-track { background: transparent; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #ccc;
  text-decoration: none;
  transition: background 0.2s;
}
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active {
  background: rgba(255,255,255,0.1);
  color: #fff;
  border-right: 3px solid #4f46e5;
}
.icon { font-size: 18px; }
.nav-divider {
  padding: 16px 20px 6px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #64748b;
}

.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.user-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}
.user-name { color: #e2e8f0; }
.user-role {
  text-transform: uppercase;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(79, 70, 229, 0.3);
  color: #a5b4fc;
}
.logout-btn {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.2);
  color: #ccc;
  border-radius: 6px;
  cursor: pointer;
}
.logout-btn:hover { background: rgba(255,255,255,0.1); }

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
</style>
