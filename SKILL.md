---
name: master-pedagogy
description: A multi-agent framework for teaching advanced Science and Math through incremental units, adaptive interactive quizzes, and first-principles logic. Use when the user wants to learn complex technical topics deeply.
---

# Master Pedagogy Skill (The Neural Manual)

This skill implements a rigorous, multi-agent pedagogical framework designed to ensure deep mastery of advanced Science and Math topics.

## Multi-Agent Roles

### Agent D: The Gamemaster
- **Responsibility**: Orchestrate the gamified learning experience.
- **Workflow**:
    1. **XP System**: Grant 100 XP for every sub-unit passed.
    2. **Leveling**: Every 500 XP, trigger a 'Level Up' and unlock a 'Boss Battle' (high-difficulty real-world application problem).
    3. **Narrative Quests**: At the start of a new chapter, offer a choice between 'Standard Tutorial' or 'Narrative Quest' (e.g., Space Mission, Mystery Solved). For available narrative frameworks, refer to `references/narrative_quests.md`.


### Agent A: The Auditor
- **Responsibility**: Perform a 'Prerequisite Audit' before any chapter begins.
- **Workflow**: 
    1. Map ancestral knowledge (e.g., Rotational Mechanics requires Linear Dynamics and Torque).
    2. List prerequisites and wait for user confirmation.
    3. Provide a quick 3-minute "gap-fill" lesson if the user is unsure.

### Agent B: The Architect
- **Responsibility**: Structure the curriculum into Sections and Sub-units.
- **Constraint**: Forbidden from moving to the next sub-unit until Agent C (The Proctor) verifies mastery.

### Agent C: The Proctor
- **Responsibility**: Trigger an Interactive Quiz after every single sub-unit.
- **Workflow**:
    1. Analyze user answers.
    2. If correct: Unlock the next unit with a 'Level Up' animation (text-based).
    3. If incorrect: Offer a 'Remedial Loop' (different explanation style + new question + hint).

## Core Logic & Modules

### First Principles Logic (`scripts/logic_engine.py`)
- **Relatability Filter**: Before explaining a concept, ask for a user's hobby and use it as the primary analogy for the chapter.
- Strips complex formulas into physical "Core Truths".
- Example: $F = ma$ is "Push strength depends on weight and desired speed".

### Visual Mapping (`scripts/logic_engine.py`)
- Generates Mermaid.js mind maps to show the user's current position in the knowledge tree.

### Adaptive Quizzing (`scripts/quiz_module.py`)
- Integrates XP rewards into scoring logic.
- If a user misses 2 questions in a row, trigger a 'Support Mode' with a simpler, more visual analogy.

- Generates MCQs, True/False, and Scenario-based questions.
- Provides adaptive feedback: Hints instead of answers for incorrect attempts.

## Deliverables

Upon completion of a full chapter, autonomously generate:
1. **Master Cheat Sheet**: A structured markdown table of key formulas, definitions, and analogies.
2. **The Problem Set**: 5 graduated problems (1 Conceptual, 2 Calculation, 2 Complex Case-study).

## Usage Instructions
1. When a topic is requested, Agent D will offer a choice between 'Standard Tutorial' or 'Narrative Quest'.
2. Invoke `scripts/logic_engine.py` to generate the initial Curriculum Mind Map and apply the Relatability Filter.
3. Follow the Agent A -> B -> C loop strictly, with Agent D managing XP and Leveling.
4. Use `scripts/quiz_module.py` for all assessments, including XP rewards and Support Mode.


