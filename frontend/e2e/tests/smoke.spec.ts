import { test, expect } from '@playwright/test'
import { ROUTES } from '../fixtures/test-data'

const smokeRoutes = [
  { name: 'Dashboard', path: ROUTES.dashboard },
  { name: 'Upload', path: ROUTES.upload },
  { name: 'Classification', path: ROUTES.classification },
  { name: 'Reconciliation', path: ROUTES.reconciliation },
  { name: 'Reports', path: ROUTES.reports },
  { name: 'Chart of Accounts', path: ROUTES.accounts },
  { name: 'Journal Entries', path: ROUTES.journalEntries },
  { name: 'General Ledger', path: ROUTES.generalLedger },
  { name: 'Financial Statements', path: ROUTES.statements },
  { name: 'Tax Bridge', path: ROUTES.taxBridge },
  { name: 'Filing Calendar', path: ROUTES.calendar },
  { name: 'AI Chat', path: ROUTES.chat },
  { name: 'Settings', path: ROUTES.settings },
]

test.describe('Smoke Tests - All Pages Load', () => {
  for (const route of smokeRoutes) {
    test(`${route.name} (${route.path}) loads without errors`, async ({ page }) => {
      const errors: string[] = []
      page.on('pageerror', (err) => errors.push(err.message))

      await page.goto(route.path)

      // Page should not redirect to login (we're authenticated)
      await page.waitForLoadState('networkidle', { timeout: 15_000 })
      expect(page.url()).not.toContain('/login')

      // No JS errors
      expect(errors).toEqual([])
    })
  }
})
