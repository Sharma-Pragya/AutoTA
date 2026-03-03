import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,         // Quiz tests depend on shared DB state
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Start both servers before running E2E tests.
  // reuseExistingServer: true allows running locally without stopping dev servers.
  webServer: [
    {
      command: '/Users/pragyasharma/anaconda3/bin/uvicorn autota.web.app:app --port 8000',
      url: 'http://localhost:8000/docs',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: 'npm run dev --prefix frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
});
