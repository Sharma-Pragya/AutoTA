import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Mock import.meta.env
vi.stubGlobal('import', { meta: { env: { VITE_INSTRUCTOR_TOKEN: '' } } });

// Import after mocking
const { joinQuiz, pollQuizStatus, submitQuiz, getQuizMeta, startQuiz, closeQuiz } =
  await import('../quiz/quizApi.js');

function mockOk(body) {
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  });
}

function mockError(status, body = {}) {
  return Promise.resolve({
    ok: false,
    status,
    json: () => Promise.resolve(body),
  });
}

describe('quizApi', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    // Reset window.location.hash
    Object.defineProperty(window, 'location', {
      value: { hash: '', origin: 'http://localhost:5173' },
      writable: true,
    });
  });

  describe('joinQuiz', () => {
    it('calls POST /api/quiz/:code/join with student_id', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ status: 'pending', problems: [] }));
      const result = await joinQuiz('TEST1', 'S1');
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/quiz/TEST1/join',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ student_id: 'S1' }),
        })
      );
      expect(result.status).toBe('pending');
    });

    it('throws with status on non-ok response', async () => {
      mockFetch.mockReturnValueOnce(mockError(403, { detail: 'Quiz is closed' }));
      await expect(joinQuiz('TEST1', 'S1')).rejects.toMatchObject({ status: 403 });
    });

    it('throws with status 404 for unknown quiz', async () => {
      mockFetch.mockReturnValueOnce(mockError(404, { detail: 'Quiz not found' }));
      await expect(joinQuiz('ZZZZZ', 'S1')).rejects.toMatchObject({ status: 404 });
    });
  });

  describe('pollQuizStatus', () => {
    it('calls GET /api/quiz/:code/status', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ status: 'active', time_remaining_seconds: 540 }));
      const result = await pollQuizStatus('TEST1');
      expect(mockFetch).toHaveBeenCalledWith('/api/quiz/TEST1/status');
      expect(result.status).toBe('active');
    });
  });

  describe('submitQuiz', () => {
    it('calls POST /api/quiz/:code/submit', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ attempt_number: 1, total_score: 0.5 }));
      const result = await submitQuiz('TEST1', 'S1', { p1: 'A' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/quiz/TEST1/submit',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ student_id: 'S1', answers: { p1: 'A' } }),
        })
      );
      expect(result.attempt_number).toBe(1);
    });

    it('throws quiz_closed error on 403', async () => {
      mockFetch.mockReturnValueOnce({ status: 403 });
      await expect(submitQuiz('TEST1', 'S1', {})).rejects.toMatchObject({
        message: 'quiz_closed',
        status: 403,
      });
    });
  });

  describe('getQuizMeta (instructor)', () => {
    it('calls GET /api/instructor/quiz/:code/meta', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ code: 'TEST1', status: 'pending' }));
      const result = await getQuizMeta('TEST1');
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/instructor/quiz/TEST1/meta',
        expect.objectContaining({ headers: expect.any(Object) })
      );
      expect(result.code).toBe('TEST1');
    });

    it('includes X-Instructor-Token header when token set in hash', async () => {
      Object.defineProperty(window, 'location', {
        value: { hash: '#token=secret123', origin: 'http://localhost:5173' },
        writable: true,
      });
      mockFetch.mockReturnValueOnce(mockOk({ code: 'TEST1' }));
      await getQuizMeta('TEST1');
      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers['X-Instructor-Token']).toBe('secret123');
    });
  });

  describe('startQuiz (instructor)', () => {
    it('calls POST /api/instructor/quiz/:code/start', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ status: 'active' }));
      await startQuiz('TEST1');
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/instructor/quiz/TEST1/start',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('closeQuiz (instructor)', () => {
    it('calls POST /api/instructor/quiz/:code/close', async () => {
      mockFetch.mockReturnValueOnce(mockOk({ status: 'closed' }));
      await closeQuiz('TEST1');
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/instructor/quiz/TEST1/close',
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});
