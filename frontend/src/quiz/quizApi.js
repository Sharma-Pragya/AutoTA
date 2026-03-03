// Quiz API wrappers
const API = '/api';

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
  const r = await fetch(`${API}/instructor/quiz/${code}/meta`);
  return r.json();
}

export async function startQuiz(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/start`, { method: 'POST' });
  return r.json();
}

export async function closeQuiz(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/close`, { method: 'POST' });
  return r.json();
}

export async function setReview(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/review`, { method: 'POST' });
  return r.json();
}

export async function getLiveStats(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/live`);
  return r.json();
}

export async function getResults(code) {
  const r = await fetch(`${API}/instructor/quiz/${code}/results`);
  return r.json();
}

export async function createQuiz(assignmentId, timeLimitSeconds = 600) {
  const r = await fetch(`${API}/instructor/quiz/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ assignment_id: assignmentId, time_limit_seconds: timeLimitSeconds }),
  });
  return r.json();
}
