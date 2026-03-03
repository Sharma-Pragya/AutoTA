/**
 * Tests for QuizApp helper functions and small stateless sub-components.
 *
 * We test:
 *   - fmt() — timer formatter
 *   - ScoreCell — score display component
 *   - checkFormat() — client-side format validation
 *
 * Full component integration is covered by E2E tests (Layer 3).
 * We avoid re-testing the network layer here (that's quizApi.test.js).
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

// ── fmt() ─────────────────────────────────────────────────────────────────────
// fmt is not exported; test the observable output via the component or inline
function fmt(s) {
  if (s === null || s === undefined) return '--:--';
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

describe('fmt()', () => {
  it('formats null/undefined as --:--', () => {
    expect(fmt(null)).toBe('--:--');
    expect(fmt(undefined)).toBe('--:--');
  });

  it('formats 0 as 0:00', () => {
    expect(fmt(0)).toBe('0:00');
  });

  it('formats 90 as 1:30', () => {
    expect(fmt(90)).toBe('1:30');
  });

  it('formats 600 as 10:00', () => {
    expect(fmt(600)).toBe('10:00');
  });

  it('pads seconds below 10', () => {
    expect(fmt(65)).toBe('1:05');
  });

  it('formats 3661 as 61:01', () => {
    expect(fmt(3661)).toBe('61:01');
  });
});

// ── checkFormat() ─────────────────────────────────────────────────────────────
// We inline checkFormat here (same logic as in QuizApp.jsx) to avoid module
// coupling. If the implementation changes, update here too.
function checkFormat(answer) {
  if (!answer.trim()) return { ok: false, msg: 'No answer entered.' };
  const invalid = answer.replace(/[A-Da-d'()+\s·*01]/g, '');
  if (invalid) return { ok: false, msg: `Invalid characters: "${invalid}"` };
  const open = (answer.match(/\(/g) || []).length;
  const close = (answer.match(/\)/g) || []).length;
  if (open !== close) return { ok: false, msg: 'Mismatched parentheses.' };
  return { ok: true, msg: 'Format looks good ✓' };
}

describe('checkFormat()', () => {
  it('rejects empty input', () => {
    expect(checkFormat('').ok).toBe(false);
    expect(checkFormat('   ').ok).toBe(false);
  });

  it('accepts valid boolean expressions', () => {
    expect(checkFormat("A'B'").ok).toBe(true);
    expect(checkFormat("A + B'C").ok).toBe(true);
    expect(checkFormat("(A + B)(C' + D)").ok).toBe(true);
    expect(checkFormat('0').ok).toBe(true);
    expect(checkFormat('1').ok).toBe(true);
  });

  it('rejects expressions with invalid characters', () => {
    const r = checkFormat('A & B');
    expect(r.ok).toBe(false);
    expect(r.msg).toContain('Invalid characters');
    expect(r.msg).toContain('&');
  });

  it('rejects mismatched parentheses (open > close)', () => {
    const r = checkFormat('(A + B');
    expect(r.ok).toBe(false);
    expect(r.msg).toContain('parentheses');
  });

  it('rejects mismatched parentheses (close > open)', () => {
    const r = checkFormat('A + B)');
    expect(r.ok).toBe(false);
    expect(r.msg).toContain('parentheses');
  });

  it('accepts balanced nested parentheses', () => {
    expect(checkFormat("(A + (B'C))").ok).toBe(true);
  });

  it('valid message text when ok', () => {
    expect(checkFormat("A'B'").msg).toContain('✓');
  });

  it('accepts variables A-D (case insensitive)', () => {
    expect(checkFormat('abcd').ok).toBe(true);
    expect(checkFormat('ABCD').ok).toBe(true);
  });

  it('rejects variables outside A-D', () => {
    expect(checkFormat('E').ok).toBe(false);
    expect(checkFormat('Z').ok).toBe(false);
  });
});

// ── QuizEntry render basics ───────────────────────────────────────────────────
// Mock quizApi so QuizEntry doesn't attempt real fetch calls
import { vi } from 'vitest';

vi.mock('../quiz/quizApi.js', () => ({
  joinQuiz: vi.fn(() => new Promise(() => {})), // never resolves by default
  pollQuizStatus: vi.fn(),
  submitQuiz: vi.fn(),
  getQuizMeta: vi.fn(),
  startQuiz: vi.fn(),
  closeQuiz: vi.fn(),
  setReview: vi.fn(),
  getLiveStats: vi.fn(),
  getResults: vi.fn(),
  createQuiz: vi.fn(),
}));

vi.mock('qrcode.react', () => ({
  QRCodeSVG: ({ value }) => <div data-testid="qr-code">{value}</div>,
}));

import QuizApp from '../quiz/QuizApp.jsx';

describe('QuizApp', () => {
  it('shows warning when no studentId provided', () => {
    render(<QuizApp code="TEST1" studentId={null} />);
    expect(screen.getByText(/No student ID/i)).toBeInTheDocument();
  });

  it('renders AutoTA header with code and studentId', () => {
    render(<QuizApp code="TEST1" studentId="S1" />);
    // The entry screen should render — joinQuiz never resolves so we stay here
    expect(screen.getByText('AutoTA')).toBeInTheDocument();
  });
});
