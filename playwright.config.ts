import { defineConfig } from '@playwright/test';

export default defineConfig({
  timeout: 30_000,
  retries: 0,
  use: { headless: true },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],
});
