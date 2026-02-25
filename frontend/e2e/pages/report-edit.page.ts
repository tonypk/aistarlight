import { type Page, type Locator, expect } from '@playwright/test'

export class ReportEditPage {
  readonly page: Page
  readonly notesInput: Locator
  readonly saveButton: Locator

  constructor(page: Page) {
    this.page = page
    this.notesInput = page.locator('.notes-input')
    this.saveButton = page.locator('.save-btn')
  }

  getField(fieldId: string): Locator {
    return this.page.locator(`[data-testid="edit-field-${fieldId}"]`)
      .or(this.page.locator(`.field-row:has(.label:has-text("${fieldId}")) .field-input`))
  }

  getFieldByLine(lineNumber: string): Locator {
    return this.page.locator(`.field-row:has(.line-no:has-text("${lineNumber}")) .field-input`)
  }

  async editField(fieldId: string, value: string) {
    const field = this.getField(fieldId)
    await field.clear()
    await field.fill(value)
  }

  async editFieldByLine(line: string, value: string) {
    const field = this.getFieldByLine(line)
    await field.clear()
    await field.fill(value)
  }

  async addNotes(text: string) {
    await this.notesInput.fill(text)
  }

  async save() {
    await this.saveButton.click()
    await expect(this.saveButton).not.toContainText('Saving', { timeout: 10_000 })
  }

  async expectFieldsVisible() {
    const firstField = this.page.locator('.field-input').first()
    await expect(firstField).toBeVisible({ timeout: 15_000 })
  }
}
