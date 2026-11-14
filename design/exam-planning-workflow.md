# Exam-Aware Study-Plan Workflow — Design Brief

## Project plan
Add a reusable MPS workflow for learners who provide an exam syllabus and exam date. MPS should verify the syllabus scope, collect a familiarity rating for every chapter/topic, separate target relevance from learner mastery, create a realistic dated study plan, and begin the first scheduled study block when the learner is ready.

## Functional specification
1. Trigger when a learner gives an exam name/profile together with a syllabus, exam date, or explicit request for a study plan. Reuse any information already supplied; ask only for missing inputs that materially affect the plan.
2. Establish the exam date, preparation start date, subjects, available study time, and any fixed constraints. Treat exam day as assessment-only or rest unless the learner asks otherwise; finish new learning before exam day.
3. Map the provided chapters/topics against current official exam guidance. Record the source and confidence. Classify scope using exactly: Core Preparation, Useful Extension, Beyond Target Level. If the official scope is broad or exact topic status is unclear, mark the item provisional and explain uncertainty rather than inventing official coverage.
4. Ask the learner for a compact familiarity status for every chapter/topic (Not started; Studied but shaky; Can explain basics; Practiced; Strong/mastered). Support batch replies, grouped chapter lists, and chunking long lists; do not force one question per chapter.
5. Track scope classification independently from learner status. A core topic can be mastered or weak; an extension can be familiar or new. Do not label a chapter mastered based on exposure or reading alone.
6. Build a dated plan through the day before the exam. Balance subjects, prioritize weak core topics, include active recall, representative practice, retrieval reviews, diagnostics/mock assessments, mistake analysis, breaks, and sleep. Compress scope according to available time; do not recommend all-nighters. Keep extensions secondary and omit beyond-target material unless explicitly requested and time allows.
7. Present the plan with date/day, subject, topics, focused blocks, practice/retrieval, assessment, and planned review. State assumptions and explain any scope trade-offs.
8. Start the first day's diagnostic or first scheduled learning block immediately when the learner says start, rather than stopping at a timetable. Adapt subsequent days to demonstrated evidence and update canonical learner state.

## MPS integration
- Add a concise decision point in `SKILL.md` after exam-profile selection and before curriculum design.
- Keep the detailed workflow in `references/exam_planning_workflow.md` and load it when syllabus/date planning is active.
- Extend the `LearnerState` specification with exam schedule, syllabus provenance, topic scope/status, and the dated plan. No database or persistence backend is added; hosts remain responsible for storage.
- Clarify that the three scope labels are based on official exam expectations, while readiness statuses are learner-specific evidence.
- Update README and CHANGELOG to describe the feature.

## Planned files
- `design/exam-planning-workflow.md` — this design record.
- `references/exam_planning_workflow.md` — operational procedure and output template.
- `SKILL.md` — trigger, state shape, workflow hook, and progress updates.
- `README.md` — capability summary.
- `CHANGELOG.md` — release note.

## Acceptance checks
- The flow reuses supplied data and asks for chapter status across the full syllabus without excessive serial questioning.
- It requires date-aware scheduling and syllabus-source validation.
- It presents Core Preparation / Useful Extension / Beyond Target Level separately from mastery status.
- It balances subject coverage and includes diagnostics, practice, reviews, and rest.
- It distinguishes a proposed plan from demonstrated mastery and adapts after results.
- Existing helper scripts and tests remain unaffected; run skill validation and the test suite after edits.
