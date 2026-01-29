import { test, expect } from '@playwright/test';

test.describe('Basic UI and Structure', () => {
  test('page loads and displays all sections', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Check that the main heading is present
    await expect(page.locator('h1')).toContainText('Polyglot WebAssembly Demo');
    
    // Check that all demo sections are present
    await expect(page.locator('text=Rust Demo')).toBeVisible();
    await expect(page.locator('text=C Demo')).toBeVisible();
    await expect(page.locator('text=WebAssembly (WAT) Demo')).toBeVisible();
    await expect(page.locator('text=Fortran Demo')).toBeVisible();
    
    // Check that buttons are present
    await expect(page.getByRole('button', { name: /Greet from Rust/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Trigger C Trap/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Add Numbers.*10.*15/i })).toBeVisible();
  });

  test('overlay element exists and is initially hidden', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Check that overlay exists but is not visible
    const overlay = page.locator('#overlay');
    await expect(overlay).toBeAttached();
    await expect(overlay).not.toBeVisible();
  });
});
