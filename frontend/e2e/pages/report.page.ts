import { type Page, type Locator, expect } from '@playwright/test'

export class ReportPage {
  readonly page: Page
  readonly formTypeSelect: Locator
  readonly periodInput: Locator
  readonly generateButton: Locator
  readonly reportTable: Locator
  readonly reportRows: Locator

  constructor(page: Page) {
    this.page = page
    this.formTypeSelect = page.locator('.form-select')
    this.periodInput = page.locator('input[type="month"]')
    this.generateButton = page.locator('.gen-btn')
    this.reportTable = page.locator('.report-list')
    this.reportRows = page.locator('.report-list tbody tr')
  }

  async goto() {
    await this.page.goto('/reports')
  }

  async generateReport(formType: string, period: string) {
    await this.formTypeSelect.selectOption(formType)
    await this.periodInput.fill(period)
    await this.generateButton.click()
    await expect(this.generateButton).not.toContainText('Generating', { timeout: 30_000 })
  }

  async expectReportsVisible() {
    await expect(this.reportTable).toBeVisible({ timeout: 10_000 })
  }

  async getReportCount(): Promise<number> {
    return this.reportRows.count()
  }
}
