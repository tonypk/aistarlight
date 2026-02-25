import { type Page, type Locator, expect } from "@playwright/test";

export class ReconciliationPage {
  readonly page: Page;
  readonly summaryButton: Locator;
  readonly detectButton: Locator;
  readonly runButton: Locator;
  readonly generateButton: Locator;
  readonly status: Locator;
  readonly controlPanel: Locator;

  constructor(page: Page) {
    this.page = page;
    this.summaryButton = page.getByRole("button", {
      name: /generate summary/i,
    });
    this.detectButton = page.getByRole("button", { name: /detect anomalies/i });
    this.runButton = page.getByRole("button", { name: /run reconciliation/i });
    this.generateButton = page.getByRole("button", {
      name: /generate report/i,
    });
    this.status = page.locator(".desc");
    this.controlPanel = page.locator(".control-panel");
  }

  async waitForSessionLoaded() {
    // Wait for the control panel to appear (indicates session detail mode, not list mode)
    await expect(this.controlPanel).toBeVisible({ timeout: 30_000 });
  }

  async waitForCompleted() {
    // Wait for the session status text to show "completed"
    await expect(this.status).toContainText("completed", { timeout: 30_000 });
  }

  async generateSummary() {
    await expect(this.summaryButton).toBeVisible({ timeout: 10_000 });
    await this.summaryButton.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
    await this.page.waitForTimeout(2000);
  }

  async detectAnomalies() {
    await expect(this.detectButton).toBeVisible({ timeout: 10_000 });
    await this.detectButton.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
    await this.page.waitForTimeout(2000);
  }

  async runReconciliation() {
    await expect(this.runButton).toBeVisible({ timeout: 10_000 });
    await this.runButton.click();
    await this.page.waitForLoadState("networkidle", { timeout: 60_000 });
    await this.page.waitForTimeout(3000);
  }

  async refreshSessionViaNavigation() {
    // Instead of hard reload (which causes empty page), use in-app navigation:
    // Click "All Sessions" → wait for session list → click back into the session
    const allSessionsBtn = this.page.getByRole("button", {
      name: /all sessions/i,
    });
    await allSessionsBtn.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });

    // Wait for session cards to appear in the list
    const sessionCard = this.page.locator(".session-card").first();
    await expect(sessionCard).toBeVisible({ timeout: 15_000 });

    // Click the first (most recent) session card to re-enter detail mode
    await sessionCard.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
    await this.waitForSessionLoaded();
  }

  async generateReport() {
    await expect(this.generateButton).toBeVisible({ timeout: 15_000 });
    await this.generateButton.click();
    await expect(this.page).toHaveURL(/\/reports\/.*\/edit/, {
      timeout: 30_000,
    });
  }
}
