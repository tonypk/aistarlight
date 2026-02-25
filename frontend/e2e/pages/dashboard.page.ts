import { type Page, type Locator, expect } from '@playwright/test'

export class DashboardPage {
  readonly page: Page
  readonly welcome: Locator
  readonly stats: Locator
  readonly quickUpload: Locator

  constructor(page: Page) {
    this.page = page
    this.welcome = page.locator('.welcome-section')
    this.stats = page.locator('.stats-row')
    this.quickUpload = page.locator('a.card[href="/upload"]')
  }

  async goto() {
    await this.page.goto('/')
  }

  async expectLoaded() {
    await expect(this.welcome).toBeVisible({ timeout: 15_000 })
  }
}
