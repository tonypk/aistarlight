import { test, expect } from "@playwright/test";
import { UploadPage } from "../pages/upload.page";
import { MappingPage } from "../pages/mapping.page";
import { ClassificationPage } from "../pages/classification.page";
import { ReconciliationPage } from "../pages/reconciliation.page";
import { ReportEditPage } from "../pages/report-edit.page";
import { TEST_FILES, REPORT_TYPES } from "../fixtures/test-data";

test.describe("CPA Workflow - Full Tax Filing Process", () => {
  test("complete flow: upload → mapping → classification → reconciliation → report", async ({
    page,
  }) => {
    test.setTimeout(300_000); // 5 minutes for entire flow

    // === Step 1: Upload SLSP Q4.xlsx ===
    const upload = new UploadPage(page);
    await upload.goto();
    await upload.selectReportType(REPORT_TYPES.BIR_2550M);
    await upload.uploadFile(TEST_FILES.SLSP_Q4);
    await upload.waitForUploadComplete();
    await expect(upload.uploadFilename).toBeVisible();
    await upload.proceedToMapping();

    // === Step 2: AI Column Mapping ===
    const mapping = new MappingPage(page);
    await mapping.runAiMapping();
    await expect(mapping.confidence).toBeVisible();
    const confidence = await mapping.getConfidencePercent();
    expect(confidence).toBeGreaterThan(50);
    await mapping.previewAndConfirm();

    // === Step 3: AI Transaction Classification ===
    const classification = new ClassificationPage(page);
    await page.waitForLoadState("networkidle", { timeout: 15_000 });
    await classification.runAiClassify();
    const txnCount = await classification.getTransactionCount();
    expect(txnCount).toBeGreaterThan(0);
    const sessionId = await classification.getSessionId();
    expect(sessionId).toBeTruthy();
    await classification.goToReconciliation();

    // === Step 4: VAT Reconciliation ===
    const recon = new ReconciliationPage(page);
    await recon.waitForSessionLoaded();

    // Capture JS errors and console messages for debugging
    const jsErrors: string[] = [];
    const consoleLogs: string[] = [];
    page.on("pageerror", (err) => jsErrors.push(err.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleLogs.push(msg.text());
    });

    await recon.generateSummary();
    await page.screenshot({ path: "test-results/debug-after-summary.png" });

    await recon.detectAnomalies();
    await page.screenshot({ path: "test-results/debug-after-detect.png" });

    await recon.runReconciliation();
    await page.screenshot({ path: "test-results/debug-after-recon.png" });

    // Debug output
    console.log(`[DEBUG] URL: ${page.url()}`);
    console.log(`[DEBUG] JS Errors: ${JSON.stringify(jsErrors)}`);
    console.log(`[DEBUG] Console Errors: ${JSON.stringify(consoleLogs)}`);
    const html = await page
      .locator("main")
      .innerHTML()
      .catch(() => "N/A");
    console.log(`[DEBUG] Main innerHTML length: ${html.length}`);
    console.log(`[DEBUG] Main content: ${html.substring(0, 500)}`);

    // === Step 5: Generate BIR 2550M Report ===
    // Wait for Generate Report button (appears when status === 'completed')
    await expect(recon.generateButton).toBeVisible({ timeout: 30_000 });
    await recon.generateReport();

    // === Step 6: Edit Report Fields ===
    const reportEdit = new ReportEditPage(page);
    await reportEdit.expectFieldsVisible();
    // Edit the first editable field (line 1 - Vatable Sales)
    await reportEdit.editFieldByLine("1", "150000");
    await reportEdit.addNotes("E2E test adjustment");
    await reportEdit.save();
  });
});
