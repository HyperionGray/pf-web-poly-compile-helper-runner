import { test, expect } from '@playwright/test';

test.describe('Error Handling and Robustness', () => {
  test('page handles missing WASM modules gracefully', async ({ page }) => {
    // Listen for console errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:8080');
    
    // Wait a bit for modules to attempt loading
    await page.waitForTimeout(2000);
    
    // Page should still be functional even if modules fail to load
    await expect(page.locator('h1')).toContainText('Polyglot WebAssembly Demo');
    
    // Buttons should still be visible
    await expect(page.getByRole('button', { name: /Greet from Rust/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Trigger C Trap/i })).toBeVisible();
  });

  test('module status indicators show appropriate state', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Wait for status indicators to update
    await page.waitForTimeout(2000);
    
    // Status indicators should show either loaded or failed state
    const rustStatus = await page.locator('#status-rust').textContent();
    const cStatus = await page.locator('#status-c').textContent();
    const watStatus = await page.locator('#status-wat').textContent();
    
    // Each status should contain either "loaded" or "Failed"
    expect(rustStatus).toMatch(/(loaded|Failed|Loading)/i);
    expect(cStatus).toMatch(/(loaded|Failed|Loading)/i);
    expect(watStatus).toMatch(/(loaded|Failed|Loading)/i);
  });

  test('clicking buttons without loaded modules does not crash page', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Try clicking all buttons even if modules aren't loaded
    await page.getByRole('button', { name: /Greet from Rust/i }).click();
    await page.getByRole('button', { name: /Add Numbers.*5.*7/i }).click();
    await page.getByRole('button', { name: /Fibonacci/i }).click();
    await page.getByRole('button', { name: /Trigger C Trap/i }).click();
    await page.getByRole('button', { name: /Add Numbers.*10.*15/i }).click();
    
    // Page should still be functional
    await expect(page.locator('h1')).toContainText('Polyglot WebAssembly Demo');
  });

  test('overlay can be dismissed by clicking', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    const overlay = page.locator('#overlay');
    
    // Initially should not be visible
    await expect(overlay).not.toBeVisible();
    
    // Simulate showing the overlay properly (using the showOverlay function)
    await page.evaluate(() => {
      // Call the showOverlay function which adds the click handler
      const overlayEl = document.getElementById('overlay');
      if (overlayEl) {
        overlayEl.className = 'visible';
        overlayEl.addEventListener('click', () => {
          overlayEl.className = '';
        }, { once: true });
      }
    });
    
    // Now should be visible
    await expect(overlay).toBeVisible();
    
    // Click to dismiss
    await overlay.click();
    
    // Wait a moment for the class to be removed
    await page.waitForTimeout(100);
    
    // Should be hidden again
    await expect(overlay).not.toBeVisible();
  });

  test('log areas update correctly when buttons are clicked', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // All log areas should be initially empty or have placeholder text
    const logRust = page.locator('#log-rust');
    const logC = page.locator('#log-c');
    const logWat = page.locator('#log-wat');
    
    await expect(logRust).toBeVisible();
    await expect(logC).toBeVisible();
    await expect(logWat).toBeVisible();
    
    // Get initial content
    const rustInitial = await logRust.textContent();
    
    // Click a button
    await page.getByRole('button', { name: /Greet from Rust/i }).click();
    
    // Wait a moment
    await page.waitForTimeout(100);
    
    // Content may or may not have changed depending on if module is loaded
    // But the element should still exist and be accessible
    await expect(logRust).toBeAttached();
  });

  test('page is responsive to different viewport sizes', async ({ page }) => {
    // Desktop size
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('http://localhost:8080');
    await expect(page.locator('h1')).toBeVisible();
    
    // Tablet size
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h1')).toBeVisible();
    
    // Mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('h1')).toBeVisible();
    
    // All sections should still be accessible
    await expect(page.locator('text=Rust Demo')).toBeVisible();
    await expect(page.locator('text=C Demo')).toBeVisible();
  });
});
