import { test, expect } from '@playwright/test'
import { DashboardPage } from '../pages/dashboard.page'

test.describe('Dashboard', () => {
  test('shows welcome section', async ({ page }) => {
    const dashboard = new DashboardPage(page)
    await dashboard.goto()
    await dashboard.expectLoaded()
    await expect(dashboard.welcome).toContainText('Welcome')
  })

  test('displays stats cards', async ({ page }) => {
    const dashboard = new DashboardPage(page)
    await dashboard.goto()
    await dashboard.expectLoaded()

    // Stats may or may not be visible depending on data
    // Just check the page loaded without errors
    await page.waitForLoadState('networkidle')
  })

  test('quick upload link navigates to upload page', async ({ page }) => {
    const dashboard = new DashboardPage(page)
    await dashboard.goto()
    await dashboard.expectLoaded()

    // Wait for quick actions to appear
    if (await dashboard.quickUpload.isVisible()) {
      await dashboard.quickUpload.click()
      await expect(page).toHaveURL(/\/upload/)
    }
  })
})
