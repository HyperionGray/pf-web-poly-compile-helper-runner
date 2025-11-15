import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const C_JS = path.resolve(process.cwd(), 'demos/pf-web-polyglot-demo-plus-c/web/wasm/c/c_trap.js');

test.describe('Polyglot + C trap', () => {
  test.skip(!fs.existsSync(C_JS), 'C artifact not built (skipping)');
  test('C __builtin_trap -> overlay', async ({ page }) => {
    await page.goto('http://localhost:8080');
    await page.getByRole('button', { name: /Trigger C Trap/i }).click();
    await expect(page.locator('#log-c')).toContainText(/Caught C trap/i);
    await expect(page.locator('#overlay')).toBeVisible();
  });
});
