import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("../views/LoginView.vue"),
      meta: { title: "Login" },
    },
    {
      path: "/sso",
      name: "sso",
      component: () => import("../views/SSOCallbackView.vue"),
      meta: { title: "SSO Login" },
    },
    {
      path: "/",
      name: "dashboard",
      component: () => import("../views/DashboardView.vue"),
      meta: { requiresAuth: true, title: "Dashboard" },
    },
    {
      path: "/upload",
      name: "upload",
      component: () => import("../views/UploadView.vue"),
      meta: { requiresAuth: true, title: "Upload Data" },
    },
    {
      path: "/receipts",
      name: "receipts",
      component: () => import("../views/ReceiptUploadView.vue"),
      meta: { requiresAuth: true, title: "Receipt Scanner" },
    },
    {
      path: "/mapping",
      name: "mapping",
      component: () => import("../views/MappingView.vue"),
      meta: { requiresAuth: true, title: "Column Mapping" },
    },
    {
      path: "/transactions",
      name: "transactions",
      component: () => import("../views/TransactionsView.vue"),
      meta: { requiresAuth: true, title: "Transactions" },
    },
    {
      path: "/classification",
      name: "classification",
      component: () => import("../views/TransactionClassificationView.vue"),
      meta: { requiresAuth: true, title: "Transaction Classification" },
    },
    {
      path: "/reconciliation",
      name: "reconciliation",
      component: () => import("../views/ReconciliationView.vue"),
      meta: { requiresAuth: true, title: "VAT Reconciliation" },
    },
    {
      path: "/bank-reconciliation",
      name: "bank-reconciliation",
      component: () => import("../views/BankReconciliationView.vue"),
      meta: { requiresAuth: true, title: "Bank Reconciliation" },
    },
    {
      path: "/reports",
      name: "reports",
      component: () => import("../views/ReportView.vue"),
      meta: { requiresAuth: true, title: "Reports" },
    },
    {
      path: "/reports/:id/edit",
      name: "report-edit",
      component: () => import("../views/ReportEditView.vue"),
      meta: { requiresAuth: true, title: "Edit Report" },
    },
    {
      path: "/chat",
      name: "chat",
      component: () => import("../views/ChatView.vue"),
      meta: { requiresAuth: true, title: "AI Tax Assistant" },
    },
    {
      path: "/knowledge",
      name: "knowledge",
      component: () => import("../views/KnowledgeView.vue"),
      meta: { requiresAuth: true, title: "Knowledge Base" },
    },
    {
      path: "/memory",
      name: "memory",
      component: () => import("../views/MemoryView.vue"),
      meta: { requiresAuth: true, title: "Memory & Preferences" },
    },
    {
      path: "/tags",
      name: "tags",
      component: () => import("../views/TagsView.vue"),
      meta: { requiresAuth: true, title: "Tags" },
    },
    {
      path: "/vendors",
      name: "vendors",
      component: () => import("../views/VendorView.vue"),
      meta: { requiresAuth: true, title: "Vendors" },
    },
    {
      path: "/suppliers",
      redirect: "/vendors",
    },
    {
      path: "/withholding",
      name: "withholding",
      component: () => import("../views/WithholdingView.vue"),
      meta: { requiresAuth: true, title: "Withholding Tax" },
    },
    {
      path: "/learning",
      name: "learning",
      component: () => import("../views/LearningInsightsView.vue"),
      meta: { requiresAuth: true, title: "Learning Insights" },
    },
    {
      path: "/calendar",
      name: "calendar",
      component: () => import("../views/FilingCalendarView.vue"),
      meta: { requiresAuth: true, title: "Filing Calendar" },
    },
    {
      path: "/compare",
      name: "compare",
      component: () => import("../views/PeriodComparisonView.vue"),
      meta: { requiresAuth: true, title: "Period Comparison" },
    },
    {
      path: "/spending",
      name: "spending",
      component: () => import("../views/SpendingDashboardView.vue"),
      meta: { requiresAuth: true, title: "Spending Dashboard" },
    },
    {
      path: "/approvals",
      name: "approvals",
      component: () => import("../views/ApprovalsView.vue"),
      meta: { requiresAuth: true, title: "Approvals" },
    },
    {
      path: "/guide",
      name: "guide",
      component: () => import("../views/GuideView.vue"),
      meta: { requiresAuth: true, title: "User Guide" },
    },
    {
      path: "/settings",
      name: "settings",
      component: () => import("../views/SettingsView.vue"),
      meta: { requiresAuth: true, title: "Settings" },
    },
    // Accounting Pipeline
    {
      path: "/accounts",
      name: "accounts",
      component: () => import("../views/ChartOfAccountsView.vue"),
      meta: { requiresAuth: true, title: "Chart of Accounts" },
    },
    {
      path: "/journal-entries",
      name: "journal-entries",
      component: () => import("../views/JournalEntriesView.vue"),
      meta: { requiresAuth: true, title: "Journal Entries" },
    },
    {
      path: "/general-ledger",
      name: "general-ledger",
      component: () => import("../views/GeneralLedgerView.vue"),
      meta: { requiresAuth: true, title: "General Ledger" },
    },
    {
      path: "/statements",
      name: "statements",
      component: () => import("../views/FinancialStatementsView.vue"),
      meta: { requiresAuth: true, title: "Financial Statements" },
    },
    {
      path: "/tax-bridge",
      name: "tax-bridge",
      component: () => import("../views/TaxBridgeView.vue"),
      meta: { requiresAuth: true, title: "Tax from GL" },
    },
    {
      path: "/penalty-calculator",
      name: "penalty-calculator",
      component: () => import("../views/PenaltyCalculatorView.vue"),
      meta: { requiresAuth: true, title: "Penalty Calculator" },
    },
    {
      path: "/form-router",
      name: "form-router",
      component: () => import("../views/FormRouterView.vue"),
      meta: { requiresAuth: true, title: "Form Router" },
    },
    {
      path: "/vendor-policies",
      name: "vendor-policies",
      component: () => import("../views/VendorPoliciesView.vue"),
      meta: { requiresAuth: true, title: "Vendor Policies" },
    },
    {
      path: "/invoices",
      name: "invoices",
      component: () => import("../views/InvoiceView.vue"),
      meta: { requiresAuth: true, title: "Invoices" },
    },
    {
      path: "/tax-prep",
      name: "tax-prep",
      component: () => import("../views/TaxPrepView.vue"),
      meta: { requiresAuth: true, title: "Prep for Taxes" },
    },
    {
      path: "/cas-compliance",
      name: "cas-compliance",
      component: () => import("../views/CASComplianceView.vue"),
      meta: { requiresAuth: true, title: "BIR CAS Compliance" },
    },
    // HR Integration
    {
      path: "/gl-mapping",
      name: "gl-mapping",
      component: () => import("../views/GLMappingView.vue"),
      meta: { requiresAuth: true, title: "Payroll GL Mapping" },
    },
    {
      path: "/integration",
      name: "integration",
      component: () => import("../views/IntegrationView.vue"),
      meta: { requiresAuth: true, title: "HR Integration" },
    },
    {
      path: "/org-dashboard",
      name: "org-dashboard",
      component: () => import("../views/OrgDashboardView.vue"),
      meta: { requiresAuth: true, title: "Organization Dashboard" },
    },
    {
      path: "/org-manage",
      name: "org-manage",
      component: () => import("../views/OrgManageView.vue"),
      meta: { requiresAuth: true, title: "Organization Management" },
    },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: "login" };
  }
});

export { router };
