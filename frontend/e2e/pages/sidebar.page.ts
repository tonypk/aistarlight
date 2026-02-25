import { type Page, type Locator, expect } from '@playwright/test'

export class SidebarPage {
  readonly page: Page
  readonly logoutButton: Locator

  constructor(page: Page) {
    this.page = page
    this.logoutButton = page.locator('.logout-btn')
  }

  getNavItem(path: string): Locator {
    return this.page.locator(`.nav-item[href="${path}"]`)
  }

  async navigateTo(path: string) {
    await this.getNavItem(path).click()
  }

  async logout() {
    await this.logoutButton.click()
    await expect(this.page).toHaveURL(/\/login/, { timeout: 10_000 })
  }
}
