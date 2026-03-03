/**
 * E2E tests for the instructor-facing quiz UI.
 *
 * Prerequisite: both servers running + QZ5A3F seeded (pending state).
 * The instructor UI at /instructor/quiz/QZ5A3F shows a control panel.
 *
 * Run with: npx playwright test tests/e2e/quiz-instructor.spec.js
 */
import { test, expect } from '@playwright/test';

const BASE  = 'http://localhost:5173';
const CODE  = 'QZ5A3F';
const ROUTE = `${BASE}/instructor/quiz/${CODE}`;


// ── Instructor quiz control panel ─────────────────────────────────────────────

test.describe('Instructor quiz control panel', () => {
  test('loads the instructor quiz page', async ({ page }) => {
    await page.goto(ROUTE);
    await expect(page).toHaveURL(ROUTE);
    // Should show AutoTA branding or instructor panel
    await expect(page.getByText('AutoTA')).toBeVisible({ timeout: 10_000 });
  });

  test('shows quiz code prominently', async ({ page }) => {
    await page.goto(ROUTE);
    await expect(page.getByText(CODE)).toBeVisible({ timeout: 10_000 });
  });

  test('shows QR code element', async ({ page }) => {
    await page.goto(ROUTE);
    // QR code is rendered as SVG
    await expect(page.locator('svg')).toBeVisible({ timeout: 10_000 });
  });

  test('shows Start Quiz button when quiz is pending', async ({ page }) => {
    await page.goto(ROUTE);
    // The instructor should see a start button (quiz starts as pending)
    await expect(
      page.getByRole('button', { name: /start quiz/i })
    ).toBeVisible({ timeout: 10_000 });
  });
});


// ── Instructor dashboard ──────────────────────────────────────────────────────

test.describe('Instructor dashboard', () => {
  test('loads the instructor dashboard', async ({ page }) => {
    await page.goto(`${BASE}/instructor`);
    await expect(page.getByText('AutoTA')).toBeVisible({ timeout: 10_000 });
  });

  test('shows navigation tabs', async ({ page }) => {
    await page.goto(`${BASE}/instructor`);
    // Dashboard should have navigation to Gradebook, Roster, etc.
    await expect(page.getByText(/Gradebook|Roster|Dashboard/i)).toBeVisible({ timeout: 10_000 });
  });

  test('shows class average or assignment summary', async ({ page }) => {
    await page.goto(`${BASE}/instructor`);
    // Summary cards or assignment table should appear
    await expect(
      page.getByText(/class average|assignments|submissions/i)
    ).toBeVisible({ timeout: 10_000 });
  });
});
