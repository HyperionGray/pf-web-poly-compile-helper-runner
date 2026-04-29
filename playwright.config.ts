import { defineConfig } from '@playwright/test';

const DEFAULT_SLOWMO = 300;
const headless = String(process.env.PF_PLAYWRIGHT_HEADLESS ?? 'false').toLowerCase() === 'true';
const parsedSlowMo = Number(process.env.PF_PLAYWRIGHT_SLOWMO ?? String(DEFAULT_SLOWMO));
const slowMo = Number.isFinite(parsedSlowMo) ? parsedSlowMo : DEFAULT_SLOWMO;

export default defineConfig({
  timeout: 30_000,
  retries: 0,
  use: {
    headless,
    launchOptions: { slowMo },
  },
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
