import { defineConfig } from '@playwright/test';

export default defineConfig({
  timeout: 30_000,
  retries: 0,
  use: { headless: true },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],
  webServer: {
    command: 'node tools/static-server.mjs web 8080',
    port: 8080,
    timeout: 10_000,
    reuseExistingServer: !process.env.CI,
  },
});
