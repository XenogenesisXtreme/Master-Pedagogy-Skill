# Advanced teaching workflows

Use this reference with the root Master Pedagogy Skill when a subject module, FHP discovery, or recovery intervention needs an explicit route. Keep the core MPS engine reusable; modules supply subject-specific content rather than duplicating learner-state or mastery code.

## Subject-module contract

Each module defines:

- prerequisites and prerequisite-audit prompts
- teaching/discovery sequence
- prediction opportunities
- appropriate diagrams, graphs, animations, and equation views
- common misconceptions
- mastery criteria and transfer checks
- remediation strategies
- exam-profile applications

MPS selects the module and route. MPVE receives only the resulting structured video context.

## Fluid Mechanics module

Use `scripts/pedagogy_modules.py` and select the `fluid-mechanics` module. Supported routes include pressure, hydrostatic pressure, Pascal's law, buoyancy/Archimedes' principle, continuity, Bernoulli, viscosity, surface tension, and fluid-flow applications.

For hydrostatic pressure, preserve this progression:

1. Audit force, area, pressure, density, units, and equilibrium prerequisites.
2. Ask a prediction about pressure at different depths.
3. Examine depth dependence with a diagram or observation.
4. Guide the learner toward `P = P₀ + ρgh`.
5. Derive it step by step and interpret every term.
6. Test direct and inverse proportionality.
7. Run a transfer check and mastery gate.
8. Remediate the diagnosed misconception with a fresh example.
9. Offer the next route or challenge.

Do not skip the audit or reveal a derivation prematurely merely because the learner says the topic is familiar. Use the selected exam profile to change application and assessment style; do not treat NEET and NSEJS as interchangeable.

## FHP interaction

FHP starts with a physical situation or prediction, then proceeds through observation, question, knowns/unknowns, assumptions, limiting case, model, derivation, sanity checks, new application, and limitations. Evaluate intermediate reasoning and correct misconceptions without jumping to the final formula.

Only set `derived: true` after the learner has completed the written derivation and MPS has verified it. Only then may MPVE visualize the derivation. Watching a video never counts as the derivation or mastery.

## Three-error recovery

The primary recovery trigger is three consecutive incorrect answers in an active concept sequence, but it is controlled by MPS:

1. Count misses per concept; two misses do not start the primary workflow.
2. At three, diagnose conceptual, mathematical, or prerequisite difficulty.
3. Decide whether motion/sequencing materially improves remediation.
4. If yes, submit one MPVE request with topic, misconception, objective, learner context, and pending mastery check.
5. Prevent duplicate requests for the same concept/misconception.
6. Deliver only a QA-passing artifact.
7. Resume the written lesson and run the pending mastery check.
8. Reset the error counter only after successful recovery or a new assessment sequence.

Use `scripts/intervention_orchestrator.py` for a durable local implementation. An unavailable backend must fall back to text, diagrams, or another teaching route without terminating the tutoring workflow.

## Runtime truthfulness

Persist state only through an actual configured store. A prompt or in-memory object is not durable cross-conversation memory. Never claim plugin/backend deployment, authentication, remote storage, narration, or session persistence unless the implementation and QA substantiate it.
