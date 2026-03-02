import { useState, useEffect, useRef, useCallback } from 'react';
import NameCheckScreen from './screens/NameCheck';
import LandingPage from './screens/Landing';
import QuestionPage from './screens/Question';
import MainPage from './screens/MainPage';
import AttestationPage from './screens/Attestation';
import ReviewPage from './screens/Review';
import { getAssignment, saveAnswer, submitAnswers, retryAssignment } from './api';
import { buildMenuStructure } from './utils';

function App() {
  const [screen, setScreen] = useState("loading");
  const [studentId, setStudentId] = useState(null);
  const [studentName, setStudentName] = useState("");
  const [assignmentData, setAssignmentData] = useState(null);
  const [problems, setProblems] = useState([]);
  const [menuGroups, setMenuGroups] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [saveStatus, setSaveStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [results, setResults] = useState(null);
  const [attestationSigned, setAttestationSigned] = useState(false);
  const [attemptId, setAttemptId] = useState(null);
  const [attemptNumber, setAttemptNumber] = useState(1);
  const [attemptStatus, setAttemptStatus] = useState("not_started");
  const [maxAttempts, setMaxAttempts] = useState(1);
  const [canRetry, setCanRetry] = useState(false);
  const [attemptsRemaining, setAttemptsRemaining] = useState(0);

  const saveTimeoutRef = useRef(null);

  // Get student ID from URL parameter
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('sid');
    if (sid) {
      setStudentId(sid);
      setScreen("namecheck");
    } else {
      setScreen("error");
    }
  }, []);

  // Load assignment data after name verification
  const loadAssignment = useCallback(async (sid) => {
    try {
      const data = await getAssignment(sid);
      setAssignmentData(data.assignment);
      setProblems(data.problems);
      setMenuGroups(buildMenuStructure(data.problems));

      // Initialize answers from existing_answers
      const initialAnswers = data.problems.map(p => data.existing_answers[p.id] || "");
      setAnswers(initialAnswers);

      // Set attempt data from API response
      setAttemptId(data.attempt?.id);
      setAttemptNumber(data.attempt?.attempt_number || data.student?.attempt_number || 1);
      setAttemptStatus(data.attempt?.status || "not_started");
      setMaxAttempts(data.assignment?.max_attempts || 1);
      setCanRetry(data.can_retry || false);
      setAttemptsRemaining(data.attempts_remaining || 0);

      return data;
    } catch (err) {
      console.error("Error loading assignment:", err);
      return null;
    }
  }, []);

  // Debounced auto-save
  const handleAnswerChange = useCallback((index, value) => {
    setAnswers(prev => {
      const newAnswers = [...prev];
      newAnswers[index] = value;
      return newAnswers;
    });

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    setSaveStatus("Saving...");

    // Set new timeout for auto-save
    saveTimeoutRef.current = setTimeout(async () => {
      try {
        await saveAnswer(studentId, problems[index].id, value);
        setSaveStatus("Saved ✓");
        setTimeout(() => setSaveStatus(""), 2000);
      } catch (err) {
        setSaveStatus("Save failed");
        console.error("Auto-save error:", err);
      }
    }, 3000); // 3 second debounce
  }, [studentId, problems]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // Build answers object
      const answersObj = {};
      problems.forEach((p, i) => {
        answersObj[p.id] = answers[i] || "";
      });

      const result = await submitAnswers(
        studentId,
        assignmentData.id,
        answersObj,
        attestationSigned,
        attemptId
      );

      setResults(result);
      setSubmitted(true);

      // Update retry info from submit response
      setCanRetry(result.can_retry || false);
      setAttemptsRemaining(result.attempts_remaining || 0);

      // Reload assignment to get updated attempt number
      await loadAssignment(studentId);
    } catch (err) {
      console.error("Submit error:", err);
      alert("Error submitting answers. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = async () => {
    try {
      const result = await retryAssignment(studentId, assignmentData.id);
      // Reload assignment with new attempt
      await loadAssignment(studentId);
      // Reset state
      setSubmitted(false);
      setResults(null);
      setAttestationSigned(false);
      setCurrentQ(0);
      setScreen("landing");
    } catch (err) {
      console.error("Retry error:", err);
      alert("Error starting new attempt. Please try again.");
    }
  };

  // Screen: Loading
  if (screen === "loading") {
    return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Sans', sans-serif" }}>
      <p>Loading...</p>
    </div>;
  }

  // Screen: Error (no student ID)
  if (screen === "error") {
    return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Sans', sans-serif" }}>
      <div style={{ textAlign: "center" }}>
        <h1 style={{ color: "#c0392b" }}>Missing Student ID</h1>
        <p>Please access this page with a valid student ID parameter.</p>
        <p style={{ fontSize: 13, color: "#666" }}>Example: ?sid=UID123456789</p>
      </div>
    </div>;
  }

  // Screen: Name check
  if (screen === "namecheck") {
    return (
      <NameCheckScreen
        studentId={studentId}
        examData={{
          course: "ECE M16",
          course_name: "Logic Design of Digital Systems",
          quarter: "Spring 2026",
          instructor: "Prof. Mani Srivastava",
          title: "Homework 5 — Karnaugh Map Simplification",
          attempt_number: attemptNumber
        }}
        onVerified={async (name) => {
          setStudentName(name);
          const data = await loadAssignment(studentId);
          if (data) {
            setScreen("landing");
          }
        }}
      />
    );
  }

  // Screen: Landing
  if (screen === "landing") {
    return (
      <LandingPage
        studentName={studentName}
        assignmentData={{
          ...assignmentData,
          menu_groups: menuGroups,
          total_parts: problems.length
        }}
        attemptNumber={attemptNumber}
        maxAttempts={maxAttempts}
        attemptStatus={attemptStatus}
        onStart={() => {
          setCurrentQ(0);
          setScreen("question");
        }}
      />
    );
  }

  // Screen: Main page
  if (screen === "main") {
    return (
      <MainPage
        problems={problems}
        answers={answers}
        menuGroups={menuGroups}
        course={assignmentData?.course || "ECE M16"}
        title={assignmentData?.title || ""}
        studentName={studentName}
        attemptNumber={attemptNumber}
        onGoToQuestion={(i) => {
          setCurrentQ(i);
          setScreen("question");
        }}
        onReview={() => setScreen("attestation")}
      />
    );
  }

  // Screen: Attestation
  if (screen === "attestation") {
    return (
      <AttestationPage
        studentName={studentName}
        onBack={() => setScreen("main")}
        onProceed={() => {
          setAttestationSigned(true);
          setScreen("review");
        }}
      />
    );
  }

  // Screen: Review
  if (screen === "review") {
    return (
      <ReviewPage
        problems={problems}
        answers={answers}
        course={assignmentData?.course || "ECE M16"}
        title={assignmentData?.title || ""}
        studentName={studentName}
        attemptNumber={attemptNumber}
        maxAttempts={maxAttempts}
        canRetry={canRetry}
        attemptsRemaining={attemptsRemaining}
        submitting={submitting}
        submitted={submitted}
        results={results}
        onGoToQuestion={(i) => {
          setCurrentQ(i);
          setScreen("question");
        }}
        onMainPage={() => setScreen("main")}
        onSubmit={handleSubmit}
        onRetry={handleRetry}
      />
    );
  }

  // Screen: Question
  const isLast = currentQ === problems.length - 1;
  return (
    <QuestionPage
      problem={problems[currentQ]}
      index={currentQ}
      total={problems.length}
      answer={answers[currentQ]}
      answers={answers}
      allProblems={problems}
      menuGroups={menuGroups}
      course={assignmentData?.course || "ECE M16"}
      title={assignmentData?.title || ""}
      studentName={studentName}
      attemptNumber={attemptNumber}
      saveStatus={saveStatus}
      onAnswerChange={(value) => handleAnswerChange(currentQ, value)}
      onNext={() => {
        if (isLast) {
          setScreen("attestation");
        } else {
          setCurrentQ(currentQ + 1);
        }
      }}
      onPrev={() => setCurrentQ(Math.max(0, currentQ - 1))}
      onMainPage={() => setScreen("main")}
      onGoToQuestion={(i) => setCurrentQ(i)}
      isLast={isLast}
    />
  );
}

export default App;
