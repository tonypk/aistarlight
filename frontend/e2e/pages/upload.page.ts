import { type Page, type Locator, expect } from '@playwright/test'

export class UploadPage {
  readonly page: Page
  readonly fileInput: Locator
  readonly reportTypeSelect: Locator
  readonly uploadProgress: Locator
  readonly uploadSuccess: Locator
  readonly uploadFilename: Locator
  readonly proceedButton: Locator

  constructor(page: Page) {
    this.page = page
    this.fileInput = page.locator('input[type="file"]')
    this.reportTypeSelect = page.locator('.report-type-select')
    this.uploadProgress = page.locator('.progress-section')
    this.uploadSuccess = page.locator('.preview-section')
    this.uploadFilename = page.locator('.file-info')
    this.proceedButton = page.locator('.proceed-btn')
  }

  async goto() {
    await this.page.goto('/upload')
  }

  async selectReportType(type: string) {
    await this.reportTypeSelect.selectOption(type)
  }

  async uploadFile(filePath: string) {
    await this.fileInput.setInputFiles(filePath)
  }

  async waitForUploadComplete() {
    await expect(this.uploadSuccess).toBeVisible({ timeout: 30_000 })
  }

  async proceedToMapping() {
    await this.proceedButton.click()
    await expect(this.page).toHaveURL(/\/mapping/, { timeout: 10_000 })
  }
}
