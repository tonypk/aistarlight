import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/tests",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  retries: process.env.CI ? 2 : 0,
  reporter: [["html", { open: "never" }]],
  use: {
    baseURL: "https://tax.clawpapa.win",
    storageState: "./e2e/.auth/user.json",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    {
      name: "setup",
      testDir: "./e2e",
      testMatch: /global-setup\.ts/,
      use: { storageState: undefined },
    },
    {
      name: "chromium",
      use: { browserName: "chromium" },
      dependencies: ["setup"],
    },
  ],
});
