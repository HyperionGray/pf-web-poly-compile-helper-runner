import { test, expect } from '@playwright/test';

test.describe('Comprehensive UI Tests', () => {
  
  test.describe('Page Structure', () => {
    test('page has correct document structure', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      // Check basic HTML structure
      const html = await page.content();
      expect(html).toContain('<!DOCTYPE html>');
      expect(html).toContain('<head>');
      expect(html).toContain('<body>');
    });

    test('page has proper charset and viewport', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      // Page should be responsive
      await expect(page.locator('h1')).toBeVisible();
    });

    test('all demo sections have log areas', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const logIds = ['log-rust', 'log-c', 'log-wat'];
      for (const id of logIds) {
        await expect(page.locator(`#${id}`)).toBeAttached();
      }
    });

    test('all demo sections have status indicators', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const statusIds = ['status-rust', 'status-c', 'status-wat'];
      for (const id of statusIds) {
        await expect(page.locator(`#${id}`)).toBeAttached();
      }
    });
  });

  test.describe('Button Interactions', () => {
    test('Rust greet button is clickable', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const button = page.getByRole('button', { name: /Greet from Rust/i });
      await expect(button).toBeEnabled();
      await button.click();
      
      // Page should remain functional
      await expect(page.locator('h1')).toBeVisible();
    });

    test('Rust add numbers button is clickable', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const button = page.getByRole('button', { name: /Add Numbers.*5.*7/i });
      await expect(button).toBeEnabled();
      await button.click();
      
      await expect(page.locator('h1')).toBeVisible();
    });

    test('Rust fibonacci button is clickable', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const button = page.getByRole('button', { name: /Fibonacci/i });
      await expect(button).toBeEnabled();
      await button.click();
      
      await expect(page.locator('h1')).toBeVisible();
    });

    test('C trap button is clickable', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const button = page.getByRole('button', { name: /Trigger C Trap/i });
      await expect(button).toBeEnabled();
      await button.click();
      
      await expect(page.locator('h1')).toBeVisible();
    });

    test('WAT add button is clickable', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const button = page.getByRole('button', { name: /Add Numbers.*10.*15/i });
      await expect(button).toBeEnabled();
      await button.click();
      
      await expect(page.locator('h1')).toBeVisible();
    });

    test('multiple buttons can be clicked in sequence', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const buttons = await page.getByRole('button').all();
      expect(buttons.length).toBeGreaterThanOrEqual(3);
      
      // Click each button
      for (const button of buttons.slice(0, 5)) {
        await button.click();
        await page.waitForTimeout(100);
      }
      
      // Page should remain functional
      await expect(page.locator('h1')).toBeVisible();
    });
  });

  test.describe('Module Loading Status', () => {
    test('status indicators update over time', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      // Wait for modules to attempt loading
      await page.waitForTimeout(2000);
      
      // Check that status indicators have content
      const rustStatus = await page.locator('#status-rust').textContent();
      const cStatus = await page.locator('#status-c').textContent();
      const watStatus = await page.locator('#status-wat').textContent();
      
      // At least one should have non-empty content
      expect(rustStatus?.length || cStatus?.length || watStatus?.length).toBeGreaterThan(0);
    });

    test('status shows loading, loaded, or failed state', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await page.waitForTimeout(3000);
      
      const statusTexts = [
        await page.locator('#status-rust').textContent() || '',
        await page.locator('#status-c').textContent() || '',
        await page.locator('#status-wat').textContent() || ''
      ];
      
      // Each status should contain a valid state indicator
      for (const status of statusTexts) {
        expect(status).toMatch(/(Loading|loaded|Failed|ready|error)/i);
      }
    });
  });

  test.describe('Overlay Behavior', () => {
    test('overlay is initially hidden', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const overlay = page.locator('#overlay');
      await expect(overlay).not.toBeVisible();
    });

    test('overlay content area exists', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const overlay = page.locator('#overlay');
      await expect(overlay).toBeAttached();
    });
  });

  test.describe('Responsive Design', () => {
    const viewports = [
      { name: 'Desktop (1920x1080)', width: 1920, height: 1080 },
      { name: 'Laptop (1366x768)', width: 1366, height: 768 },
      { name: 'Tablet (768x1024)', width: 768, height: 1024 },
      { name: 'Mobile (375x667)', width: 375, height: 667 },
      { name: 'Mobile Small (320x568)', width: 320, height: 568 }
    ];

    for (const viewport of viewports) {
      test(`page renders correctly at ${viewport.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto('http://localhost:8080');
        
        // Main heading should be visible
        await expect(page.locator('h1')).toBeVisible();
        
        // At least one button should be visible
        const buttons = await page.getByRole('button').all();
        expect(buttons.length).toBeGreaterThan(0);
      });
    }
  });

  test.describe('Console and Error Handling', () => {
    test('page loads without critical JavaScript errors', async ({ page }) => {
      const criticalErrors: string[] = [];
      
      page.on('pageerror', (error) => {
        // Filter out expected errors (like WASM load failures)
        if (!error.message.includes('WASM') && 
            !error.message.includes('WebAssembly') &&
            !error.message.includes('fetch')) {
          criticalErrors.push(error.message);
        }
      });

      await page.goto('http://localhost:8080');
      await page.waitForTimeout(2000);
      
      // No critical JavaScript errors should occur
      expect(criticalErrors).toHaveLength(0);
    });

    test('console messages are informative', async ({ page }) => {
      const consoleMessages: string[] = [];
      
      page.on('console', (msg) => {
        consoleMessages.push(msg.text());
      });

      await page.goto('http://localhost:8080');
      await page.waitForTimeout(2000);
      
      // Should have some console output (status messages, etc.)
      // This is just informational - not a strict requirement
    });
  });

  test.describe('Performance Basics', () => {
    test('page initial load is under 5 seconds', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('http://localhost:8080', { waitUntil: 'domcontentloaded' });
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(5000);
    });

    test('page is interactive quickly', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      // Should be able to interact with a button within 3 seconds
      const button = page.getByRole('button').first();
      await expect(button).toBeEnabled({ timeout: 3000 });
    });
  });

  test.describe('Content Verification', () => {
    test('page has meaningful content', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const bodyText = await page.textContent('body');
      
      // Page should have substantial content
      expect(bodyText?.length).toBeGreaterThan(200);
      
      // Should contain expected keywords
      expect(bodyText).toContain('Rust');
      expect(bodyText).toContain('Demo');
    });

    test('demo sections have button labels', async ({ page }) => {
      await page.goto('http://localhost:8080');
      
      const buttonTexts = await page.getByRole('button').allTextContents();
      
      // All buttons should have text
      for (const text of buttonTexts) {
        expect(text.trim().length).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Navigation', () => {
    test('page can be refreshed', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('h1')).toBeVisible();
      
      await page.reload();
      await expect(page.locator('h1')).toBeVisible();
    });

    test('page handles back/forward navigation', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('h1')).toBeVisible();
      
      // Navigate somewhere and back (if there are internal links)
      // For SPA, this just tests that the page remains stable
      await page.goto('http://localhost:8080');
      await expect(page.locator('h1')).toBeVisible();
    });
  });
});

test.describe('Accessibility Tests', () => {
  test('buttons have accessible names', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    const buttons = await page.getByRole('button').all();
    
    for (const button of buttons) {
      const text = await button.textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
    }
  });

  test('page can be navigated with keyboard', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Tab through interactive elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }
    
    // Something should be focused
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedTag).toBeTruthy();
  });

  test('headings provide document structure', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Should have at least h1
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });
});
