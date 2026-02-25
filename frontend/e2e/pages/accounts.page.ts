import { type Page, type Locator, expect } from '@playwright/test'

export class AccountsPage {
  readonly page: Page
  readonly seedButton: Locator
  readonly groups: Locator

  constructor(page: Page) {
    this.page = page
    this.seedButton = page.getByRole('button', { name: /seed/i })
    this.groups = page.locator('.account-groups')
  }

  async goto() {
    await this.page.goto('/accounts')
  }

  async seedAccounts() {
    await this.seedButton.click()
    await expect(this.groups).toBeVisible({ timeout: 15_000 })
  }

  async expectGroupsVisible() {
    await expect(this.groups).toBeVisible({ timeout: 10_000 })
  }
}
