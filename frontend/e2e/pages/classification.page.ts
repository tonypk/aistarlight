import { type Page, type Locator, expect } from '@playwright/test'

export class ClassificationPage {
  readonly page: Page
  readonly aiButton: Locator
  readonly status: Locator
  readonly toReconButton: Locator
  readonly txnTable: Locator
  readonly txnRows: Locator

  constructor(page: Page) {
    this.page = page
    this.aiButton = page.locator('button', { hasText: /AI Classify/i })
    this.status = page.locator('.desc')
    this.toReconButton = page.locator('button', { hasText: /Continue to Reconciliation/i })
    this.txnTable = page.locator('.table-wrapper table')
    this.txnRows = page.locator('.table-wrapper tbody tr')
  }

  async runAiClassify() {
    await expect(this.aiButton).toBeVisible({ timeout: 10_000 })
    await this.aiButton.click()

    // Wait for classifying to finish (button text goes back to "AI Classify")
    await expect(this.aiButton).toContainText('AI Classify', { timeout: 60_000 })

    // Wait for transactions to load (loading message disappears)
    await this.page.waitForFunction(
      () => !document.body.textContent?.includes('Loading transactions'),
      { timeout: 30_000 },
    )

    // Give the page a moment to re-render the status
    await this.page.waitForTimeout(2000)
  }

  async getTransactionCount(): Promise<number> {
    const text = await this.status.textContent()
    const match = text?.match(/(\d+)\s*transactions/)
    return match ? parseInt(match[1], 10) : 0
  }

  async getSessionId(): Promise<string> {
    const url = this.page.url()
    const match = url.match(/session=([^&]+)/)
    return match ? match[1] : ''
  }

  async goToReconciliation() {
    await this.toReconButton.click()
    await expect(this.page).toHaveURL(/\/reconciliation/, { timeout: 10_000 })
  }
}
