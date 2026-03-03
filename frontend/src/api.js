// API utility functions for AutoTA frontend

const API_BASE = '/api';

export async function verifyName(studentId, name) {
  const response = await fetch(`${API_BASE}/verify-name`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, name }),
  });
  return response.json();
}

export async function getAssignment(studentId) {
  const response = await fetch(`${API_BASE}/assignment/${studentId}`);
  return response.json();
}

export async function saveAnswer(studentId, problemId, answer) {
  const response = await fetch(`${API_BASE}/save-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: studentId, problem_id: problemId, answer }),
  });
  return response.json();
}

export async function submitAnswers(studentId, assignmentId, answers, attestationSigned, attemptId) {
  const response = await fetch(`${API_BASE}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: studentId,
      assignment_id: assignmentId,
      answers,
      attestation_signed: attestationSigned,
      attempt_id: attemptId,
    }),
  });
  return response.json();
}

export async function retryAssignment(studentId, assignmentId) {
  const response = await fetch(`${API_BASE}/retry/${studentId}/${assignmentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  return response.json();
}

// ── Instructor API ──────────────────────────────────────────────────────────

export async function getInstructorDashboard() {
  const response = await fetch(`${API_BASE}/instructor/dashboard`);
  return response.json();
}

export async function getInstructorGradebook() {
  const response = await fetch(`${API_BASE}/instructor/gradebook`);
  return response.json();
}

export async function getInstructorAssignment(assignmentId) {
  const response = await fetch(`${API_BASE}/instructor/assignment/${assignmentId}`);
  return response.json();
}

export async function getInstructorStudent(studentId) {
  const response = await fetch(`${API_BASE}/instructor/student/${studentId}`);
  return response.json();
}

export async function getInstructorRoster() {
  const response = await fetch(`${API_BASE}/instructor/roster`);
  return response.json();
}
