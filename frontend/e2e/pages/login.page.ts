import { type Page, type Locator, expect } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator
  readonly errorMessage: Locator
  readonly toggleLink: Locator

  constructor(page: Page) {
    this.page = page
    this.emailInput = page.getByPlaceholder('you@company.com')
    this.passwordInput = page.getByPlaceholder('Enter password')
    this.submitButton = page.getByRole('button', { name: /sign in|create account/i })
    this.errorMessage = page.locator('.error')
    this.toggleLink = page.locator('.toggle a')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }

  async expectError(text?: string) {
    await expect(this.errorMessage).toBeVisible()
    if (text) {
      await expect(this.errorMessage).toContainText(text)
    }
  }
}
