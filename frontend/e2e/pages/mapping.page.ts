import { type Page, type Locator, expect } from '@playwright/test'

export class MappingPage {
  readonly page: Page
  readonly aiButton: Locator
  readonly confidence: Locator
  readonly previewButton: Locator
  readonly confirmButton: Locator

  constructor(page: Page) {
    this.page = page
    this.aiButton = page.locator('.ai-btn')
    this.confidence = page.locator('.confidence-badge')
    this.previewButton = page.locator('.confirm-btn', { hasText: 'Preview' })
    this.confirmButton = page.locator('.confirm-btn', { hasText: 'Confirm' })
  }

  async goto() {
    await this.page.goto('/mapping')
  }

  async runAiMapping() {
    await this.aiButton.click()
    // Wait for AI to complete (button text changes back)
    await expect(this.aiButton).not.toContainText('analyzing', { timeout: 45_000 })
  }

  async getConfidencePercent(): Promise<number> {
    const text = await this.confidence.textContent()
    const match = text?.match(/(\d+)%/)
    return match ? parseInt(match[1], 10) : 0
  }

  async previewAndConfirm() {
    await this.previewButton.click()
    await expect(this.confirmButton).toBeVisible({ timeout: 5_000 })
    await this.confirmButton.click()
    await expect(this.page).toHaveURL(/\/classification/, { timeout: 10_000 })
  }
}
