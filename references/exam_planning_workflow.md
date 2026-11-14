# Exam-Aware Study Planning Workflow

Load this reference whenever a learner provides an exam syllabus and date, requests an exam study plan, or wants a multi-day preparation schedule.

## 1. Trigger and intake

Use details already present in the conversation or attached plan. Do not ask the learner to repeat them. Establish the target exam, exam date, start date, syllabus or chapter list, subjects, and realistic daily study availability. Ask only for missing details that materially change the schedule. If availability is unknown, offer a reasonable provisional schedule and state the assumption rather than blocking useful work.

If the learner has provided a long syllabus, first normalize it into a compact, subject-grouped chapter list. Preserve the learner's own chapter names where possible. Separate genuine chapters from subtopics only when that helps planning.

## 2. Verify and classify the syllabus scope

Before calling a topic exam-required, check the current official exam authority's syllabus, brochure, or notice. Prefer topic-level official documents. If the authority only gives a broad grade-level scope, say so; use the provided syllabus and reliable official context to make provisional topic classifications, clearly marking those that cannot be verified at chapter level. Past papers can indicate question style and emphasis, but must not be presented as an official syllabus.

Assign each chapter or subtopic one scope label:

- **Core Preparation** — explicitly included in the official syllabus or clearly within its stated required level and scope.
- **Useful Extension** — not clearly required or above the usual depth, but may strengthen prerequisites, transfer, or preparation for adjacent topics.
- **Beyond Target Level** — clearly outside the exam's stated scope or substantially beyond its expected level.

For each uncertain or non-obvious assignment, retain a short rationale and source/evidence. If evidence is insufficient, say “provisional—verify” rather than claiming certainty. Never silently promote a broad syllabus interpretation into a guaranteed topic-by-topic official list.

## 3. Ask for chapter familiarity in one manageable pass

After showing the normalized chapter list and its scope labels, ask how prepared the learner feels for **each** chapter. Explain that scope and familiarity are separate: a Core topic can be mastered or weak, and an Extension can be familiar or new.

Use a compact rating key:

- **N — Not started**
- **S — Studied, but shaky**
- **B — Can explain the basics**
- **P — Practiced and can solve standard questions**
- **M — Strong / can solve independently and explain why**

Invite a single grouped reply such as `Physics: Friction P, WPE S; Chemistry: Atoms B, Mole concept N`. For very long syllabi, batch by subject or a manageable number of chapters and maintain a pending list. Accept natural-language equivalents and previously demonstrated evidence; do not demand the exact letters. Ask one follow-up only when a rating is ambiguous or a key scheduling constraint is missing.

Do not treat self-reported “M” as verified mastery. Record it as self-assessed until an explanation, representative question set, or timed checkpoint provides evidence. Keep the initial assessment low-stakes and use it to plan, not to shame or rank.

## 4. Convert syllabus and readiness into priorities

Keep two dimensions distinct for every topic:

1. **Exam relevance:** Core Preparation / Useful Extension / Beyond Target Level, with a brief source-based rationale.
2. **Learner readiness:** Not started / Learning / Needs practice / Revision required / Mastered, with source of evidence (self-report, diagnostic, practice, or demonstrated mastery).

Set priorities in this order unless the exam format or learner's constraints justify a change:

1. Weak or unseen Core Preparation topics and prerequisites.
2. Core topics needing practice, retrieval, or correction of recurring errors.
3. Strong Core topics, scheduled for concise spaced review rather than reteaching.
4. Useful Extensions only after the core route is secure and time permits.
5. Beyond Target Level topics omitted by default; include only if explicitly requested and the learner has remaining time.

Use an initial diagnostic when broad readiness is unknown, but do not let a diagnostic consume the whole first study day. Revise priorities after each assessment.

## 5. Build a realistic dated plan

Schedule from the preparation start date through the day before the exam. If the exam date has already passed, confirm the intended future exam before generating a dated plan. Account for the learner's local dates and stated commitments. Do not put new learning on the exam day by default.

For each date, provide a clear agenda with subjects, specific chapters/subtopics, estimated focused time, active-recall or problem-solving tasks, and a short check for evidence of learning. Balance subjects across the available days. In a short window, prioritize representative breadth in Core Preparation over exhaustive coverage of one area. Revisit difficult topics after a delay and preserve time for a mixed mock or sectional checkpoints, error analysis, final retrieval, breaks, and adequate sleep. Do not recommend all-nighters or claim that passive video watching counts as focused study.

Let the learner's available time govern workload. Do not assume a universal number of study hours. If the learner requests a very intensive schedule, organize it into focused blocks with breaks and a clear stop time; flag when the requested volume is unlikely to be sustainable or complete.

A useful day structure may include: a short retrieval warm-up; new or weak Core topic learning; worked examples; independent questions; another subject block; mixed practice; and an end-of-day mistake-log/retrieval review. Adapt the number and length of blocks rather than copying a fixed template.

## 6. Present the result

Show the plan in a compact date-by-date format. For each day include:

- Main learning objectives and the exact topics.
- Scope label where it affects prioritization.
- Focused study blocks or time estimates.
- Practice, retrieval, and an assessment checkpoint.
- Any scheduled revisit or prerequisite repair.

Before the schedule, briefly state the exam date, available preparation days, study-time assumption, and any syllabus uncertainty. After the schedule, state the few highest-priority trade-offs, such as extensions deferred to protect Core coverage. Avoid claiming every listed topic is guaranteed to appear.

## 7. Start teaching and adapt

Once the learner says `start` (or clearly asks to begin), begin the scheduled first-day diagnostic or lesson immediately. Do not merely restate the plan. Keep explanations efficient and exam-oriented while maintaining the chosen pedagogy and mastery gates. End each day with a concise progress report, updated mistake log, readiness changes backed by evidence, and the next day's priorities.

Adapt the plan when the learner demonstrates strength or weakness: skip reteaching mastered concepts, shorten review for strong topics, add targeted remediation for repeated misconceptions, and redistribute remaining study time without sacrificing all subjects to one difficult chapter. Preserve the reason for each changed priority.

## Suggested plan-state fields

Store only what the host can actually persist. Extend the canonical learner state with an optional plan object such as:

# Fragment inside `LearnerState.learning`:
```yaml
exam_plan:
  exam_name: null
  exam_date: null
  preparation_start_date: null
  available_focused_hours_per_day: null
  constraints: []
  syllabus_sources: []
  scope_notes: []
  topics:
    - subject: null
      chapter: null
      scope_class: null # Core Preparation | Useful Extension | Beyond Target Level
      scope_rationale: null
      scope_source: null
      readiness_status: null # Not started | Learning | Needs practice | Revision required | Mastered
      readiness_evidence: null # self-report | diagnostic | practice | demonstrated
      confidence: null
      priority: null
      next_review: null
  dated_schedule: []
```

This is a state specification, not a database or persistence implementation. Preserve the existing concept-level mastery record and never overwrite demonstrated learning with a schedule estimate.
