import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages/login.page'
import { DashboardPage } from '../pages/dashboard.page'
import { SidebarPage } from '../pages/sidebar.page'
import { TEST_USER } from '../fixtures/test-data'

test.describe('Authentication', () => {
  test('successful login redirects to dashboard', async ({ browser }) => {
    // Use fresh context without stored auth
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    const loginPage = new LoginPage(page)
    const dashboardPage = new DashboardPage(page)

    await loginPage.goto()
    await loginPage.login(TEST_USER.email, TEST_USER.password)
    await dashboardPage.expectLoaded()

    await context.close()
  })

  test('wrong password shows error', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()
    const loginPage = new LoginPage(page)

    await loginPage.goto()
    await loginPage.login(TEST_USER.email, 'WrongPassword123')
    await loginPage.expectError()

    await context.close()
  })

  test('unauthenticated access redirects to login', async ({ browser }) => {
    const context = await browser.newContext({ storageState: undefined })
    const page = await context.newPage()

    await page.goto('/reports')
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 })

    await context.close()
  })

  test('logout clears session', async ({ page }) => {
    const sidebar = new SidebarPage(page)

    await page.goto('/')
    await sidebar.logout()
    await expect(page).toHaveURL(/\/login/)

    // Verify we can't access protected routes after logout
    await page.goto('/reports')
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 })
  })
})
