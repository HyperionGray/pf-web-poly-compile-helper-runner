import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const C_JS = path.resolve(process.cwd(), 'demos/pf-web-polyglot-demo-plus-c/web/wasm/c/c_trap.js');
const RUST_PKG = path.resolve(process.cwd(), 'demos/pf-web-polyglot-demo-plus-c/web/wasm/rust/pkg/rust_demo.js');
const WAT_WASM = path.resolve(process.cwd(), 'demos/pf-web-polyglot-demo-plus-c/web/wasm/asm/mini.wasm');

test.describe('Polyglot WebAssembly Demo', () => {
  test('page loads and shows module loading status', async ({ page }) => {
    await page.goto('http://localhost:8080');
    
    // Check that status indicators are present
    await expect(page.locator('#status-rust')).toBeVisible();
    await expect(page.locator('#status-c')).toBeVisible();
    await expect(page.locator('#status-wat')).toBeVisible();
    
    // Check that log areas exist
    await expect(page.locator('#log-rust')).toBeAttached();
    await expect(page.locator('#log-c')).toBeAttached();
    await expect(page.locator('#log-wat')).toBeAttached();
  });

  test.describe('C Module', () => {
    test.skip(!fs.existsSync(C_JS), 'C artifact not built (skipping)');
    
    test('C module loads successfully', async ({ page }) => {
      await page.goto('http://localhost:8080');
      // Wait for module to load
      await expect(page.locator('#status-c')).toContainText(/loaded/i, { timeout: 10000 });
    });

    test('C __builtin_trap -> overlay', async ({ page }) => {
      await page.goto('http://localhost:8080');
      // Wait for C module to load
      await expect(page.locator('#status-c')).toContainText(/loaded/i, { timeout: 10000 });
      
      await page.getByRole('button', { name: /Trigger C Trap/i }).click();
      await expect(page.locator('#log-c')).toContainText(/Caught C trap/i);
      await expect(page.locator('#overlay')).toBeVisible();
    });
  });

  test.describe('Rust Module', () => {
    test.skip(!fs.existsSync(RUST_PKG), 'Rust artifact not built (skipping)');
    
    test('Rust module loads successfully', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-rust')).toContainText(/loaded/i, { timeout: 10000 });
    });

    test('Rust greet function works', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-rust')).toContainText(/loaded/i, { timeout: 10000 });
      
      await page.getByRole('button', { name: /Greet from Rust/i }).click();
      await expect(page.locator('#log-rust')).toContainText(/Hello.*World/i);
    });

    test('Rust add function works', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-rust')).toContainText(/loaded/i, { timeout: 10000 });
      
      await page.getByRole('button', { name: /Add Numbers/i }).click();
      await expect(page.locator('#log-rust')).toContainText(/5.*7.*12/i);
    });

    test('Rust fibonacci function works', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-rust')).toContainText(/loaded/i, { timeout: 10000 });
      
      await page.getByRole('button', { name: /Fibonacci/i }).click();
      await expect(page.locator('#log-rust')).toContainText(/Fibonacci.*10.*55/i);
    });
  });

  test.describe('WAT Module', () => {
    test.skip(!fs.existsSync(WAT_WASM), 'WAT artifact not built (skipping)');
    
    test('WAT module loads successfully', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-wat')).toContainText(/loaded/i, { timeout: 10000 });
    });

    test('WAT add function works', async ({ page }) => {
      await page.goto('http://localhost:8080');
      await expect(page.locator('#status-wat')).toContainText(/loaded/i, { timeout: 10000 });
      
      await page.getByRole('button', { name: /Add Numbers.*10.*15/i }).click();
      await expect(page.locator('#log-wat')).toContainText(/10.*15.*25/i);
    });
  });
});
