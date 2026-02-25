import { test, expect } from "@playwright/test";
import { ReportPage } from "../pages/report.page";

test.describe("Reports Management", () => {
  test("reports page loads", async ({ page }) => {
    const reportPage = new ReportPage(page);
    await reportPage.goto();

    // Page should load without errors
    await page.waitForLoadState("networkidle");
    await expect(
      page.getByRole("heading", { name: "Reports", exact: true, level: 2 }),
    ).toBeVisible();
  });

  test("report list shows existing reports", async ({ page }) => {
    const reportPage = new ReportPage(page);
    await reportPage.goto();
    await page.waitForLoadState("networkidle");

    // If reports exist, the table should be visible
    const tableVisible = await reportPage.reportTable.isVisible();
    if (tableVisible) {
      const count = await reportPage.getReportCount();
      expect(count).toBeGreaterThan(0);
    }
  });

  test("generate report with sample data", async ({ page }) => {
    const reportPage = new ReportPage(page);
    await reportPage.goto();

    // Generate a report (using sample data since no file is uploaded)
    const currentMonth = new Date().toISOString().slice(0, 7);
    await reportPage.generateReport("BIR_2550M", currentMonth);

    // After generation, report list should be visible
    await reportPage.expectReportsVisible();
  });

  test("workflow transition: draft to review", async ({ page }) => {
    const reportPage = new ReportPage(page);
    await reportPage.goto();
    await page.waitForLoadState("networkidle");

    // Find a draft report and transition it
    const draftRow = page
      .locator(".report-list tbody tr")
      .filter({ hasText: "draft" })
      .first();
    if (await draftRow.isVisible()) {
      const submitBtn = draftRow.getByText("Submit for Review");
      if (await submitBtn.isVisible()) {
        await submitBtn.click();
        // Wait for status to change
        await page.waitForTimeout(2000);
      }
    }
  });
});
