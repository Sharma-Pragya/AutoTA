AutoTA — System Architecture
Overview
AutoTA is an LLM-powered parameterized assessment platform for STEM courses. It generates unique problem variants per student, verifies solutions computationally, delivers them via a web interface, and supports unlimited retries with fresh problems.
The system is decomposed into four layers. Each layer is independently deployable and communicates through well-defined interfaces (JSON objects and Python function signatures). No layer depends on the internal implementation of another.

Layer 1: Generation Engine
Purpose: Turn a problem specification into N unique, verified problem variants with solutions.
Inputs:

Problem spec (YAML): topic, constraints, parameter ranges, answer format, reference material path
Reference material (optional): past assignments, lecture notes, textbook excerpts for style/difficulty calibration

Outputs:

List of ProblemVariant JSON objects, each containing: variant_id, problem_text, parameters, solution, answer_format, metadata
Generation report: total attempted, passed verification, failed, retried

Components:
ComponentRoleLLM?Prompt BuilderConstructs system + user prompt from spec + reference materialNoGeneratorCalls Claude API, parses structured JSON responseYesVerifier (from Layer 3)Checks each generated solution against parametersNoOrchestratorCoordinates generate → verify → retry loopNoVariant RegistryRecords which variants exist, prevents parameter collisionsNo
Flow:
Spec YAML
  → Prompt Builder (adds reference material, output schema, constraints)
  → Claude API (returns JSON array of variants)
  → Parse into ProblemVariant objects
  → For each variant:
      → Verifier.verify(variant)
      → If PASS: write to output
      → If FAIL: collect error, re-prompt with feedback ("minterm 5 evaluates wrong")
  → Write report
Batching strategy: For N > 10 variants, split into batches of 10 per API call. Each batch prompt includes previously generated parameter sets to avoid duplicates.
Retry strategy: Failed variants get up to 2 regeneration attempts. The retry prompt includes the specific verification error so the LLM can correct the mistake. After max retries, variant is marked failed in the report and skipped.

Layer 2: Web UI / Renderer
Purpose: Deliver problems to students in a browser. Collect and submit answers. Display feedback.
Inputs:

Assigned variant (fetched from variant registry by student ID)
Grading results (from Layer 3)

Outputs:

Rendered problem with structured input fields
Student submission (forwarded to Layer 3)
Score + feedback display

Components:
ComponentRoleFastAPI BackendServes API endpoints: get assignment, submit answer, get scoreReact FrontendRenders problems, input forms, feedback. Responsive (phone/tablet for QR quizzes)Auth ModuleGoogle OAuth / UCLA SSO. Maps authenticated user to student IDFormat ValidatorClient-side regex check before submission (e.g., valid Boolean expression syntax)Session ManagerTracks active quiz sessions, enforces time limits
Key design decisions:
Self-contained multi-part problems: If a problem has parts A, B, C, and Part B depends on Part A's answer, the system shows the correct answer for Part A when displaying Part B. Students never cascade errors from one part to the next. Each part is independently gradeable.
No Jupyter: Problems render as structured HTML with purpose-built input fields (text boxes for expressions, grids for truth tables, dropdowns for multiple choice). No notebook cells, no cell deletion, no formatting breakage.
QR Quiz mode: Instructor triggers a timed quiz session. System generates a QR code pointing to the quiz URL. Students scan, get a unique variant, answer within the time limit. Backend enforces the timer server-side, not client-side.
API contract (backend endpoints):
GET  /api/assignment/{student_id}          → ProblemVariant (minus solution)
POST /api/submit/{student_id}/{variant_id} → GradeResult + Feedback
GET  /api/score/{student_id}/{variant_id}  → GradeResult
POST /api/retry/{student_id}               → New ProblemVariant (triggers Layer 4)
GET  /api/quiz/session/{session_id}        → Quiz metadata + assigned variant
POST /api/quiz/start                       → Creates session, returns QR URL (instructor only)

Layer 3: Grading & Verification
Purpose: Determine if a student's answer is correct. Also used at generation time to verify LLM-produced solutions.
Inputs:

Student submission (answer string/object)
Problem variant (parameters + solution from variant registry)

Outputs:

GradeResult: score (0-1 float), feedback (str), confidence ("deterministic" | "llm_assisted" | "human_reviewed"), flagged (bool)

Three-tier grading architecture:
Tier 1: Deterministic (preferred)
Pure Python. No LLM. Instant. Free. 100% reliable.
Used for: Boolean expressions, truth tables, numerical answers, matrix operations, set comparisons, multiple choice.
How it works: Compare student answer against solution using domain-specific logic. Boolean expressions → evaluate both against full truth table. Matrices → element-wise comparison with tolerance. Sets → set equality.
These are the same verifier classes used in Layer 1 for generation verification. Dual-purpose: verify generated solutions AND grade student submissions.
Tier 2: LLM-Assisted (fallback)
Claude API call. 2-5 seconds. ~$0.01-0.05 per submission. ~90-95% accurate.
Used for: Open-ended explanations, design justifications, partial credit scenarios, problem types without a deterministic verifier.
How it works: Send student answer + correct solution + rubric to Claude. Prompt asks for a score, reasoning, and confidence level. If confidence is below threshold, flag for human review.
Tier 3: Human Review (exception)
TA reviews flagged submissions. Can confirm or override LLM grade.
How it works: Flagged items appear in a review queue (initially a JSON file, later a Discord notification or web dashboard). TA sees the problem, student answer, LLM's grade, and LLM's reasoning. TA clicks approve or overrides with a new score.
Verifier interface:
pythonclass Verifier(ABC):
    @abstractmethod
    def verify(self, variant: ProblemVariant) -> VerificationResult:
        """Verify that the variant's solution is correct for its parameters.
        Used at generation time (Layer 1)."""

    @abstractmethod
    def grade(self, variant: ProblemVariant, submission: str) -> GradeResult:
        """Grade a student submission against the variant's solution.
        Used at submission time (Layer 2 → Layer 3)."""

    @property
    @abstractmethod
    def problem_type(self) -> str:
        """String key matching the spec's problem_type field."""

    @property
    def confidence_level(self) -> str:
        return "deterministic"
```

**Verifier registry:** Maps `problem_type` string → Verifier class. Orchestrator and grading endpoint both look up the verifier by type. If no deterministic verifier exists for a problem type, falls back to Tier 2 (LLM grading).

**Initial verifiers to implement:**
| problem_type | Verification method | Grading method |
|---|---|---|
| `kmap_simplification` | Truth table evaluation | Truth table evaluation |
| `boolean_expression` | Truth table evaluation | Truth table evaluation |
| `truth_table` | Row-by-row comparison | Row-by-row comparison |
| `number` | Numerical equality with tolerance | Numerical equality with tolerance |
| `multiple_choice` | Exact match | Exact match |

---

## Layer 4: Retry Loop

**Purpose:** Enable unlimited retries with fresh problem instances. Track attempts. Aggregate scores.

**Inputs:**
- Retry request from student (via Layer 2)
- Current attempt history from attempt tracker

**Outputs:**
- New variant assignment (triggers Layer 1 if needed, or draws from pre-generated pool)
- Updated attempt record

**Components:**

| Component | Role |
|---|---|
| Attempt Tracker | Logs each attempt: student_id, variant_id, score, timestamp |
| Pool Manager | Maintains a pool of pre-generated variants per problem spec. Draws from pool on retry. If pool depleted, triggers Layer 1 to generate more. |
| Exclusion Filter | Ensures a student never sees the same parameter set twice. Passes prior parameter sets as constraints to Layer 1. |
| Score Aggregator | Computes final grade from multiple attempts. Configurable policy: best score, average of top N, most recent, weighted decay. Default: best score. |
| Analytics Collector | Tracks per-problem metrics: average attempts to pass, common errors, score distribution across attempts. |

**Flow:**
```
Student clicks "New Attempt"
  → Attempt Tracker logs current attempt
  → Exclusion Filter compiles list of prior parameter sets
  → Pool Manager checks for available unused variant
      → If available: assign it
      → If empty: call Layer 1 with exclusion constraints to generate fresh variants
  → Variant Registry records new assignment
  → Layer 2 renders new problem
```

**Scoring policies (configurable per assignment):**
- `best`: Final grade = highest score across all attempts (default)
- `latest`: Final grade = most recent attempt
- `average_top_n`: Final grade = average of top N scores
- `decaying`: Each attempt weighted less (1.0, 0.9, 0.8, ...), take max

**Pre-generation strategy:** For known assignments (homework distributed in advance), pre-generate a pool of 3× expected students (e.g., 210 variants for 70 students, assuming ~3 attempts average). Pool refills asynchronously if it drops below a threshold.

---

## Cross-Layer Feature: QR Quiz System

This feature orchestrates all four layers for in-class formative assessment.

**Flow:**
```
1. Instructor: POST /api/quiz/start {topic, duration, num_variants}
2. Layer 1 generates variant pool (pre-warmed or on-demand)
3. Backend returns QR code URL
4. Instructor displays QR in lecture
5. Student scans → Layer 2 authenticates, assigns variant, records attendance
6. Student answers on phone within time limit
7. Layer 3 grades instantly (deterministic)
8. Timer expires → Backend compiles class summary
9. Instructor sees: "72% correct. Common error: missed edge-wrap grouping."
```

**Timer enforcement:** Server-side. Client displays a countdown but the backend rejects submissions after deadline. Prevents clock manipulation.

**Attendance:** Scanning the QR and loading the quiz page counts as attendance, regardless of whether the student submits an answer. Separate attendance record from grade record.

---

## Data Flow Summary
```
                    ┌─────────────┐
                    │  Spec YAML  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Layer 1   │
                    │ Generation  │◄──── Claude API
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Layer 3   │
                    │ Verification│      (deterministic Python)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Variant    │
                    │  Registry   │      (JSON files → later SQLite)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐    │     ┌──────▼──────┐
       │   Layer 2   │    │     │   Layer 4   │
       │   Web UI    │    │     │ Retry Loop  │
       └──────┬──────┘    │     └──────┬──────┘
              │            │            │
              │      ┌─────▼─────┐      │
              └─────►│  Layer 3  │◄─────┘
                     │  Grading  │
                     └───────────┘

Build Phases
PhaseLayersDeliverableInterfacePhase 1Layer 1 + Layer 3 (verify only)CLI: generate N verified variants from a specCommand linePhase 2Layer 2Web UI: student views problem, submits answerBrowserPhase 3Layer 3 (grading)Deterministic + LLM grading on submissionsAPIPhase 4Layer 4Retry loop with fresh variants, score aggregationAPI + UIPhase 5Cross-layerQR quiz system, analytics, Discord botFull stack
We are building Phase 1 now. Everything above Layer 1 + Layer 3 verification is documented for architectural context but should not be implemented yet.

Storage Strategy
Phase 1 (now): Everything is JSON files on disk. Specs in specs/. Variants in output/{problem_type}/. No database.
Phase 2+: SQLite for variant registry and attempt tracking. Single file, no server, easy to back up. Schema migration path to PostgreSQL if we ever need multi-server deployment (we won't for a long time).
Never in the repo: Course materials, solution keys, student data, API keys, generated variants. All gitignored.
