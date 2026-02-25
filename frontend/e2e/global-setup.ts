import { test as setup, expect } from "@playwright/test";
import { TEST_USER } from "./fixtures/test-data";

setup("authenticate", async ({ page }) => {
  await page.goto("/login");

  // Use placeholder-based selectors as fallback (works with or without data-testid)
  const emailInput = page.getByPlaceholder("you@company.com");
  const passwordInput = page.getByPlaceholder("Enter password");
  const submitButton = page.getByRole("button", { name: /sign in/i });

  await emailInput.fill(TEST_USER.email);
  await passwordInput.fill(TEST_USER.password);
  await submitButton.click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL("/", { timeout: 15_000 });
  await expect(page.locator("text=Welcome")).toBeVisible({ timeout: 10_000 });

  // Save auth state
  await page.context().storageState({ path: "./e2e/.auth/user.json" });
});
