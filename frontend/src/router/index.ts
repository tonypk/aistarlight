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
      path: "/register",
      name: "register",
      component: () => import("../views/RegisterView.vue"),
      meta: { title: "Register" },
    },
    {
      path: "/verify-email",
      name: "verify-email",
      component: () => import("../views/VerifyEmailView.vue"),
      meta: { title: "Verify Email" },
    },
    {
      path: "/",
      component: () => import("../components/layout/DashboardLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "dashboard",
          component: () => import("../views/DashboardView.vue"),
          meta: { title: "Dashboard" },
        },
        {
          path: "upload",
          name: "upload",
          component: () => import("../views/UploadView.vue"),
          meta: { title: "Upload Data" },
        },
        {
          path: "receipts",
          name: "receipts",
          component: () => import("../views/ReceiptUploadView.vue"),
          meta: { title: "Receipt Scanner" },
        },
        {
          path: "mapping",
          name: "mapping",
          component: () => import("../views/MappingView.vue"),
          meta: { title: "Column Mapping" },
        },
        {
          path: "transactions",
          name: "transactions",
          component: () => import("../views/TransactionsView.vue"),
          meta: { title: "Transactions" },
        },
        {
          path: "classification",
          name: "classification",
          component: () => import("../views/TransactionClassificationView.vue"),
          meta: { title: "Transaction Classification" },
        },
        {
          path: "reconciliation",
          name: "reconciliation",
          component: () => import("../views/ReconciliationView.vue"),
          meta: { title: "VAT Reconciliation" },
        },
        {
          path: "bank-reconciliation",
          name: "bank-reconciliation",
          component: () => import("../views/BankReconciliationView.vue"),
          meta: { title: "Bank Reconciliation" },
        },
        {
          path: "reports",
          name: "reports",
          component: () => import("../views/ReportView.vue"),
          meta: { title: "Reports" },
        },
        {
          path: "reports/:id/edit",
          name: "report-edit",
          component: () => import("../views/ReportEditView.vue"),
          meta: { title: "Edit Report" },
        },
        {
          path: "chat",
          name: "chat",
          component: () => import("../views/ChatView.vue"),
          meta: { title: "AI Tax Assistant" },
        },
        {
          path: "knowledge",
          name: "knowledge",
          component: () => import("../views/KnowledgeView.vue"),
          meta: { title: "Knowledge Base" },
        },
        {
          path: "memory",
          name: "memory",
          component: () => import("../views/MemoryView.vue"),
          meta: { title: "Memory & Preferences" },
        },
        {
          path: "tags",
          name: "tags",
          component: () => import("../views/TagsView.vue"),
          meta: { title: "Tags" },
        },
        {
          path: "vendors",
          name: "vendors",
          component: () => import("../views/VendorView.vue"),
          meta: { title: "Vendors" },
        },
        {
          path: "suppliers",
          redirect: "/vendors",
        },
        {
          path: "withholding",
          name: "withholding",
          component: () => import("../views/WithholdingView.vue"),
          meta: { title: "Withholding Tax" },
        },
        {
          path: "learning",
          name: "learning",
          component: () => import("../views/LearningInsightsView.vue"),
          meta: { title: "Learning Insights" },
        },
        {
          path: "calendar",
          name: "calendar",
          component: () => import("../views/FilingCalendarView.vue"),
          meta: { title: "Filing Calendar" },
        },
        {
          path: "compare",
          name: "compare",
          component: () => import("../views/PeriodComparisonView.vue"),
          meta: { title: "Period Comparison" },
        },
        {
          path: "spending",
          name: "spending",
          component: () => import("../views/SpendingDashboardView.vue"),
          meta: { title: "Spending Dashboard" },
        },
        {
          path: "approvals",
          name: "approvals",
          component: () => import("../views/ApprovalsView.vue"),
          meta: { title: "Approvals" },
        },
        {
          path: "guide",
          name: "guide",
          component: () => import("../views/GuideView.vue"),
          meta: { title: "User Guide" },
        },
        {
          path: "settings",
          name: "settings",
          component: () => import("../views/SettingsView.vue"),
          meta: { title: "Settings" },
        },
        {
          path: "accounts",
          name: "accounts",
          component: () => import("../views/ChartOfAccountsView.vue"),
          meta: { title: "Chart of Accounts" },
        },
        {
          path: "journal-entries",
          name: "journal-entries",
          component: () => import("../views/JournalEntriesView.vue"),
          meta: { title: "Journal Entries" },
        },
        {
          path: "general-ledger",
          name: "general-ledger",
          component: () => import("../views/GeneralLedgerView.vue"),
          meta: { title: "General Ledger" },
        },
        {
          path: "statements",
          name: "statements",
          component: () => import("../views/FinancialStatementsView.vue"),
          meta: { title: "Financial Statements" },
        },
        {
          path: "tax-bridge",
          name: "tax-bridge",
          component: () => import("../views/TaxBridgeView.vue"),
          meta: { title: "Tax from GL" },
        },
        {
          path: "penalty-calculator",
          name: "penalty-calculator",
          component: () => import("../views/PenaltyCalculatorView.vue"),
          meta: { title: "Penalty Calculator" },
        },
        {
          path: "form-router",
          name: "form-router",
          component: () => import("../views/FormRouterView.vue"),
          meta: { title: "Form Router" },
        },
        {
          path: "vendor-policies",
          name: "vendor-policies",
          component: () => import("../views/VendorPoliciesView.vue"),
          meta: { title: "Vendor Policies" },
        },
        {
          path: "invoices",
          name: "invoices",
          component: () => import("../views/InvoiceView.vue"),
          meta: { title: "Invoices" },
        },
        {
          path: "tax-prep",
          name: "tax-prep",
          component: () => import("../views/TaxPrepView.vue"),
          meta: { title: "Prep for Taxes" },
        },
        {
          path: "cas-compliance",
          name: "cas-compliance",
          component: () => import("../views/CASComplianceView.vue"),
          meta: { title: "BIR CAS Compliance" },
        },
        {
          path: "gl-mapping",
          name: "gl-mapping",
          component: () => import("../views/GLMappingView.vue"),
          meta: { title: "Payroll GL Mapping" },
        },
        {
          path: "integration",
          name: "integration",
          component: () => import("../views/IntegrationView.vue"),
          meta: { title: "HR Integration" },
        },
        {
          path: "org-dashboard",
          name: "org-dashboard",
          component: () => import("../views/OrgDashboardView.vue"),
          meta: { title: "Organization Dashboard" },
        },
        {
          path: "org-manage",
          name: "org-manage",
          component: () => import("../views/OrgManageView.vue"),
          meta: { title: "Organization Management" },
        },
        // Expense Management
        {
          path: "expenses",
          name: "expenses",
          component: () => import("../views/expenses/ExpenseListView.vue"),
          meta: { title: "My Expenses" },
        },
        {
          path: "expenses/new",
          name: "expense-new",
          component: () => import("../views/expenses/ExpenseFormView.vue"),
          meta: { title: "New Expense" },
        },
        {
          path: "expenses/approvals",
          name: "expense-approvals",
          component: () => import("../views/expenses/ApprovalQueueView.vue"),
          meta: { title: "Expense Approvals" },
        },
        {
          path: "expenses/finance",
          name: "expense-finance",
          component: () => import("../views/expenses/FinanceQueueView.vue"),
          meta: { title: "Finance Queue" },
        },
        {
          path: "expenses/policies",
          name: "expense-policies",
          component: () => import("../views/expenses/PolicyManageView.vue"),
          meta: { title: "Expense Policies" },
        },
        {
          path: "expenses/approvers",
          name: "expense-approvers",
          component: () => import("../views/expenses/ApproverManageView.vue"),
          meta: { title: "Expense Approvers" },
        },
        {
          path: "expenses/analytics",
          name: "expense-analytics",
          component: () => import("../views/expenses/ExpenseAnalyticsView.vue"),
          meta: { title: "Expense Analytics" },
        },
        {
          path: "expenses/:id",
          name: "expense-detail",
          component: () => import("../views/expenses/ExpenseDetailView.vue"),
          meta: { title: "Expense Detail" },
        },
        {
          path: "expenses/:id/edit",
          name: "expense-edit",
          component: () => import("../views/expenses/ExpenseFormView.vue"),
          meta: { title: "Edit Expense" },
        },
      ],
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
