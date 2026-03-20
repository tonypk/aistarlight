<script setup lang="ts">
import { h, computed, ref, onMounted, onUnmounted, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout, NLayoutSider, NLayoutHeader, NLayoutContent,
  NMenu, NIcon, NButton, NSpace, NAvatar, NDropdown, NSwitch, NSelect,
  NBadge, NPopover, NList, NListItem, NThing, NEmpty, NTime,
  type MenuOption,
} from 'naive-ui'
import {
  HomeOutline, ChatbubblesOutline, CloudUploadOutline, ReceiptOutline,
  CardOutline, BusinessOutline, PricetagsOutline, CheckmarkCircleOutline,
  BookOutline, CreateOutline, DocumentTextOutline, BarChartOutline,
  LinkOutline, MapOutline, CalendarOutline, AlertCircleOutline,
  DocumentOutline, ShieldCheckmarkOutline, SearchOutline, WalletOutline,
  FlashOutline, LibraryOutline, SchoolOutline, ClipboardOutline,
  ScaleOutline, SettingsOutline, PersonOutline, LogOutOutline,
  SunnyOutline, MoonOutline, NotificationsOutline, PeopleOutline,
  HelpCircleOutline, GridOutline, BulbOutline, CalculatorOutline,
} from '@vicons/ionicons5'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'
import { useAgentStore } from '../../stores/agent'
import { useNotificationStore } from '../../stores/notification'
import AIPanel from '../ai/AIPanel.vue'
import AITrigger from '../ai/AITrigger.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const ui = useUIStore()
const agentStore = useAgentStore()
const notifStore = useNotificationStore()

// --- Notifications ---
const showNotifications = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

function onNotifPopoverUpdate(visible: boolean) {
  showNotifications.value = visible
  if (visible) notifStore.fetchNotifications()
}

onMounted(() => {
  auth.initUser()
  auth.fetchCompanies()
  notifStore.fetchUnreadCount()
  pollTimer = setInterval(() => notifStore.fetchUnreadCount(), 60000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

// --- Menu helpers ---
const ROLE_LEVEL: Record<string, number> = {
  viewer: 1,
  accountant: 2,
  admin: 3,
  company_admin: 3,
  owner: 4,
}
const userLevel = computed(() => ROLE_LEVEL[auth.currentRole] || 1)
function hasAccess(minRole: string): boolean {
  return userLevel.value >= (ROLE_LEVEL[minRole] || 1)
}

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

function mi(label: string, key: string, icon: Component, minRole = 'viewer'): MenuOption | null {
  if (!hasAccess(minRole)) return null
  return { label, key, icon: renderIcon(icon) }
}

function filterNull(items: (MenuOption | null)[]): MenuOption[] {
  return items.filter((x): x is MenuOption => x !== null)
}

const menuOptions = computed<MenuOption[]>(() => {
  const groups: MenuOption[] = []

  // Workspace
  const workspace = filterNull([
    mi('Dashboard', 'dashboard', HomeOutline),
    mi('AI Chat', 'chat', ChatbubblesOutline),
  ])
  if (workspace.length) {
    groups.push({ type: 'group', label: 'Workspace', key: 'g-workspace', children: workspace })
  }

  // Data & Transactions
  const data = filterNull([
    mi('Upload Data', 'upload', CloudUploadOutline, 'accountant'),
    mi('Receipt Scanner', 'receipts', ReceiptOutline, 'accountant'),
    mi('Transactions', 'transactions', CardOutline),
    mi('Vendors', 'vendors', BusinessOutline, 'accountant'),
    mi('Classification', 'classification', PricetagsOutline, 'accountant'),
    mi('Tags', 'tags', PricetagsOutline, 'accountant'),
    mi('Approvals', 'approvals', CheckmarkCircleOutline, 'accountant'),
  ])
  if (data.length) {
    groups.push({ type: 'group', label: 'Data & Transactions', key: 'g-data', children: data })
  }

  // Accounting
  const accounting = filterNull([
    mi('Chart of Accounts', 'accounts', BookOutline, 'accountant'),
    mi('Journal Entries', 'journal-entries', CreateOutline, 'accountant'),
    mi('General Ledger', 'general-ledger', DocumentTextOutline, 'accountant'),
    mi('Financial Statements', 'statements', BarChartOutline, 'accountant'),
    mi('HR Integration', 'integration', LinkOutline, 'admin'),
    mi('GL Mapping', 'gl-mapping', MapOutline, 'admin'),
  ])
  if (accounting.length) {
    groups.push({ type: 'group', label: 'Accounting', key: 'g-accounting', children: accounting })
  }

  // Tax & Filing
  const tax = filterNull([
    mi('Prep for Taxes', 'tax-prep', ClipboardOutline, 'accountant'),
    mi('Invoices', 'invoices', ReceiptOutline, 'accountant'),
    mi('Tax from GL', 'tax-bridge', CalculatorOutline, 'accountant'),
    mi('Reports', 'reports', DocumentOutline),
    mi('Form Router', 'form-router', MapOutline),
    mi('Filing Calendar', 'calendar', CalendarOutline),
    mi('Penalty Calculator', 'penalty-calculator', AlertCircleOutline, 'accountant'),
    mi('Withholding Tax', 'withholding', DocumentTextOutline, 'accountant'),
    mi('CAS Compliance', 'cas-compliance', ShieldCheckmarkOutline, 'accountant'),
  ])
  if (tax.length) {
    groups.push({ type: 'group', label: 'Tax & Filing', key: 'g-tax', children: tax })
  }

  // Reconciliation
  const recon = filterNull([
    mi('Reconciliation', 'reconciliation', SearchOutline, 'accountant'),
    mi('Bank Recon', 'bank-reconciliation', WalletOutline, 'accountant'),
  ])
  if (recon.length) {
    groups.push({ type: 'group', label: 'Reconciliation', key: 'g-recon', children: recon })
  }

  // More (agents + extras)
  const more = filterNull([
    mi('Filing Agent', 'agent-filing', FlashOutline),
    mi('Recon Agent', 'agent-recon', SearchOutline),
    mi('Journal Agent', 'agent-journal', CreateOutline),
    mi('Compliance Agent', 'agent-compliance', ShieldCheckmarkOutline),
    mi('Knowledge', 'knowledge', LibraryOutline),
    mi('Learning Insights', 'learning', SchoolOutline),
    mi('Vendor Policies', 'vendor-policies', ClipboardOutline, 'accountant'),
    mi('Spending', 'spending', WalletOutline),
    mi('Period Compare', 'compare', ScaleOutline),
  ])
  if (more.length) {
    groups.push({ type: 'group', label: 'More', key: 'g-more', children: more })
  }

  // Connected Apps
  const crossApp = filterNull([
    mi('HR & Payroll', 'cross-hr', PeopleOutline, 'admin'),
  ])
  if (crossApp.length) {
    groups.push({ type: 'group', label: 'Connected Apps', key: 'g-cross', children: crossApp })
  }

  // System
  const system = filterNull([
    mi('Organization', 'org-dashboard', GridOutline, 'admin'),
    mi('Memory', 'memory', BulbOutline, 'admin'),
    mi('User Guide', 'guide', HelpCircleOutline),
    mi('Settings', 'settings', SettingsOutline, 'admin'),
  ])
  if (system.length) {
    groups.push({ type: 'group', label: 'System', key: 'g-system', children: system })
  }

  return groups
})

const activeKey = computed(() => route.name as string)

function handleMenuClick(key: string) {
  // Agent shortcuts
  if (key === 'agent-filing') { agentStore.openPanel('filing'); return }
  if (key === 'agent-recon') { agentStore.openPanel('recon'); return }
  if (key === 'agent-journal') { agentStore.openPanel('journal'); return }
  if (key === 'agent-compliance') { agentStore.openPanel('compliance'); return }
  // Cross-app
  if (key === 'cross-hr') { window.open('https://hr.halaos.com', '_blank'); return }
  // Normal navigation
  router.push({ name: key })
}

// --- Company Switcher ---
const companyOptions = computed(() =>
  auth.companies.map(c => ({ label: c.company_name, value: c.tenant_id }))
)
const currentTenantId = computed(() => auth.user?.tenant_id || '')

async function handleSwitchCompany(tenantId: string) {
  if (tenantId && tenantId !== auth.user?.tenant_id) {
    await auth.switchCompany(tenantId)
    router.push('/')
  }
}

// --- User dropdown ---
const userMenuOptions = [
  { label: 'Profile', key: 'profile', icon: renderIcon(PersonOutline) },
  { type: 'divider', key: 'd' },
  { label: 'Logout', key: 'logout', icon: renderIcon(LogOutOutline) },
]

function handleUserAction(key: string) {
  if (key === 'logout') {
    auth.logout()
    router.push({ name: 'login' })
  } else if (key === 'profile') {
    router.push({ name: 'settings' })
  }
}
</script>

<template>
  <NLayout has-sider style="min-height: 100vh">
    <NLayoutSider
      bordered
      :width="260"
      :collapsed-width="64"
      show-trigger
      collapse-mode="width"
      :collapsed="ui.sidebarCollapsed"
      @update:collapsed="(val: boolean) => ui.sidebarCollapsed = val"
    >
      <div style="padding: 16px 20px; font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
        HalaOS
        <span style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(37, 99, 235, 0.15); color: #3b82f6;">
          {{ auth.jurisdiction }}
        </span>
      </div>

      <!-- Company Switcher -->
      <div v-if="companyOptions.length > 1 && !ui.sidebarCollapsed" style="padding: 0 12px 8px;">
        <NSelect
          :value="currentTenantId"
          :options="companyOptions"
          size="small"
          @update:value="handleSwitchCompany"
        />
      </div>
      <div v-else-if="auth.user && !ui.sidebarCollapsed" style="padding: 0 20px 8px; font-size: 13px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
        {{ auth.user.company_name }}
      </div>

      <NMenu
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuClick"
        :collapsed="ui.sidebarCollapsed"
        :collapsed-width="64"
        :collapsed-icon-size="20"
      />
    </NLayoutSider>

    <NLayout>
      <NLayoutHeader bordered style="height: 56px; display: flex; align-items: center; justify-content: flex-end; padding: 0 24px;">
        <NSpace align="center" :size="16">
          <!-- Notifications -->
          <NPopover trigger="click" placement="bottom-end" :show="showNotifications" @update:show="onNotifPopoverUpdate" style="width: 380px; padding: 0;">
            <template #trigger>
              <NBadge :value="notifStore.unreadCount" :max="99" :show="notifStore.unreadCount > 0">
                <NButton quaternary circle>
                  <template #icon><NIcon :component="NotificationsOutline" /></template>
                </NButton>
              </NBadge>
            </template>
            <div style="padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--n-border-color);">
              <strong>Notifications</strong>
              <NButton text size="small" @click="notifStore.markAllRead()" v-if="notifStore.unreadCount > 0">Mark all read</NButton>
            </div>
            <div style="max-height: 400px; overflow-y: auto;">
              <NEmpty v-if="notifStore.notifications.length === 0" description="No notifications" style="padding: 24px;" />
              <NList v-else hoverable clickable>
                <NListItem
                  v-for="n in notifStore.notifications"
                  :key="n.id"
                  :style="{ opacity: n.is_read ? 0.6 : 1, background: n.is_read ? 'transparent' : 'var(--n-color-hover)' }"
                  @click="notifStore.markRead(n.id)"
                >
                  <NThing :title="n.title" :description="n.message" content-style="margin-top: 4px;">
                    <template #footer>
                      <NTime :time="new Date(n.created_at)" type="relative" />
                    </template>
                  </NThing>
                </NListItem>
              </NList>
            </div>
          </NPopover>

          <!-- Theme toggle -->
          <NSwitch :value="ui.isDark" @update:value="ui.toggleDarkMode()">
            <template #checked>
              <NIcon :component="MoonOutline" />
            </template>
            <template #unchecked>
              <NIcon :component="SunnyOutline" />
            </template>
          </NSwitch>

          <!-- User dropdown -->
          <NDropdown :options="userMenuOptions" @select="handleUserAction">
            <NButton quaternary>
              <NSpace align="center" :size="8">
                <NAvatar :size="28" round>{{ auth.user?.full_name?.charAt(0) || auth.user?.email?.charAt(0) || 'U' }}</NAvatar>
                <span>{{ auth.user?.full_name || auth.user?.email }}</span>
              </NSpace>
            </NButton>
          </NDropdown>
        </NSpace>
      </NLayoutHeader>

      <NLayoutContent style="padding: 24px;">
        <router-view />
      </NLayoutContent>
    </NLayout>

    <!-- Finance-specific: AI Panel -->
    <AITrigger />
    <AIPanel />
  </NLayout>
</template>
