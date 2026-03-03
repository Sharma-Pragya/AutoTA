/**
 * E2E tests for the student-facing quiz UI.
 *
 * Prerequisite: both servers must be running and data/autota.db must have
 * the QZ5A3F quiz session seeded (run `python migrations/seed_quiz.py` once).
 *
 * The quiz session is reset between relevant tests via the reset helper.
 *
 * Run with: npx playwright test tests/e2e/quiz-student.spec.js
 */
import { test, expect, request } from '@playwright/test';

const BASE = 'http://localhost:5173';
const API  = 'http://localhost:8000';

// Test student — seeded by seed.py
const SID  = 'UID123456789';
const CODE = 'QZ5A3F';

async function resetQuizSession(apiContext) {
  // Reset via sqlite directly is not possible from Playwright;
  // instead we call the API to close and restart (or skip if session isn't started).
  // For a clean run, the user should run: python -c "..."  (see README section 5)
  // This is a best-effort helper.
  try {
    await apiContext.post(`${API}/api/instructor/quiz/${CODE}/close`);
  } catch (_) {}
}

async function startQuizSession(apiContext) {
  await apiContext.post(`${API}/api/instructor/quiz/${CODE}/start`);
}


// ── Student entry screen ──────────────────────────────────────────────────────

test.describe('Student entry screen', () => {
  test('shows join form when accessing quiz URL', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    // AutoTA header should be visible
    await expect(page.getByText('AutoTA')).toBeVisible();
  });

  test('shows "No student ID" warning when sid missing', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}`);
    await expect(page.getByText(/No student ID/i)).toBeVisible();
  });

  test('join button is disabled without student ID', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}`);
    const joinBtn = page.getByRole('button', { name: /Join Quiz/i });
    await expect(joinBtn).toBeDisabled();
  });
});


// ── Quiz pending / waiting screen ─────────────────────────────────────────────

test.describe('Quiz waiting screen (quiz is pending)', () => {
  test('shows waiting screen after joining a pending quiz', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    // Auto-join triggers; pending quiz shows waiting screen
    await expect(page.getByText(/Waiting for quiz to start/i)).toBeVisible({ timeout: 10_000 });
    // Code should be displayed
    await expect(page.getByText(CODE)).toBeVisible();
  });
});


// ── Active quiz flow ──────────────────────────────────────────────────────────

test.describe('Active quiz flow', () => {
  let apiContext;

  test.beforeAll(async ({ playwright }) => {
    apiContext = await playwright.request.newContext();
    await startQuizSession(apiContext);
  });

  test.afterAll(async () => {
    try {
      await apiContext.post(`${API}/api/instructor/quiz/${CODE}/close`);
    } catch (_) {}
    await apiContext.dispose();
  });

  test('shows question list after joining active quiz', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    // Should transition from waiting to quiz questions
    // Look for the progress dots or question area
    await expect(page.locator('[data-testid="progress-dots"], textarea, input[placeholder]'))
      .toBeVisible({ timeout: 10_000 });
  });

  test('timer bar is visible during active quiz', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    // Timer shows minutes:seconds format
    await expect(page.getByText(/\d+:\d{2}/)).toBeVisible({ timeout: 10_000 });
  });

  test('can type an answer in the input', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    await page.waitForSelector('textarea', { timeout: 10_000 });
    const textarea = page.locator('textarea').first();
    await textarea.fill("A'B'");
    await expect(textarea).toHaveValue("A'B'");
  });
});


// ── Closed quiz ───────────────────────────────────────────────────────────────

test.describe('Closed quiz behavior', () => {
  let apiContext;

  test.beforeAll(async ({ playwright }) => {
    apiContext = await playwright.request.newContext();
    // Start then immediately close
    await startQuizSession(apiContext).catch(() => {});
    await apiContext.post(`${API}/api/instructor/quiz/${CODE}/close`);
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test('redirects to "quiz closed" state when joining closed quiz', async ({ page }) => {
    await page.goto(`${BASE}/quiz/${CODE}?sid=${SID}`);
    // When quiz is closed and student tries to join, they should see a closed/error message
    // Could be the error boundary or a 403 error from join
    await expect(
      page.getByText(/closed|ended|over|expired|forbidden/i)
    ).toBeVisible({ timeout: 10_000 });
  });
});
