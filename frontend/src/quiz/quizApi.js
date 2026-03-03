// Quiz API wrappers
const API = '/api';

// Instructor token — set VITE_INSTRUCTOR_TOKEN in .env.local for dev,
// or pass via the URL hash (#token=...) for quick classroom use.
function getInstructorToken() {
  if (typeof window !== 'undefined') {
    const hash = new URLSearchParams(window.location.hash.slice(1));
    if (hash.get('token')) return hash.get('token');
  }
  return import.meta.env.VITE_INSTRUCTOR_TOKEN || '';
}

function instructorHeaders() {
  const token = getInstructorToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'X-Instructor-Token': token } : {}),
  };
}

export async function joinQuiz(code, studentId) {
  const r = await fetch(`${API}/quiz/${code}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId }),
  });
  if (!r.ok) throw Object.assign(new Error('join failed'), { status: r.status, body: await r.json() });
  return r.json();
}

export async function pollQuizStatus(code) {
  const r = await fetch(`${API}/quiz/${code}/status`);
  return r.json();
}

export async function submitQuiz(code, studentId, answers) {
  const r = await fetch(`${API}/quiz/${code}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, answers }),
  });
  if (r.status === 403) throw Object.assign(new Error('quiz_closed'), { status: 403 });
  return r.json();
}

export async function getQuizMeta(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/meta`, {
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function startQuiz(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/start`, {
    method: 'POST',
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function closeQuiz(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/close`, {
    method: 'POST',
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function setReview(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/review`, {
    method: 'POST',
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function getLiveStats(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/live`, {
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function getResults(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/results`, {
    headers: instructorHeaders(),
  });
  return r.json();
}

export async function createQuiz(assignmentId, timeLimitSeconds = 600) {
  const r = await fetch(`${API}/instructor/quiz/create`, {
    method: 'POST',
    headers: instructorHeaders(),
    body: JSON.stringify({ assignment_id: assignmentId, time_limit_seconds: timeLimitSeconds }),
  });
  return r.json();
}
