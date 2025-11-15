import { test, expect } from '@playwright/test';

test('cautionary traps + overlay', async ({ page }) => {
  await page.goto('http://localhost:8082');
  await page.getByRole('button', { name: /Trigger Trap/i }).click();
  await expect(page.locator('#log-unreach')).toContainText(/Caught trap/i);
  await page.getByRole('button', { name: /Trigger OOB/i }).click();
  await expect(page.locator('#log-oob')).toContainText(/Caught trap/i);
  await page.getByRole('button', { name: /Show Faux Crash/i }).click();
  await expect(page.locator('#overlay')).toBeVisible();
});
