# Subject-module architecture

MPS keeps one learner-state, assessment, and mastery engine. Subject modules provide route data and subject-specific teaching decisions without duplicating the core tutor.

## Module contract

`SubjectModule` defines an identifier, subject, description, supported exam profiles, and named `TopicRoute` objects. Each route supplies prerequisites, a discovery/teaching sequence, prediction prompts, visual formats, common misconceptions, mastery criteria, remediation strategies, and profile-specific applications.

The registry is implemented in `scripts/pedagogy_modules.py`:

```python
from scripts.pedagogy_modules import default_registry

module = default_registry().select("Physics", "hydrostatic pressure")
route = module.route_for("hydrostatic pressure")
```

## Implemented module: Fluid Mechanics

The first complete module is `fluid-mechanics`. It includes routes for:

- pressure
- hydrostatic pressure
- Pascal's law
- buoyancy and Archimedes' principle
- continuity equation
- Bernoulli's principle
- viscosity
- surface tension
- fluid-flow applications

Hydrostatic pressure explicitly progresses from force/area prerequisites and a depth prediction through `P = P₀ + ρgh`, term interpretation, proportionality checks, transfer, mastery, and misconception remediation.

The module distinguishes NEET and NSEJS applications while also exposing General and JEE routes. It does not replace the root MPS state or mastery engine.

## Extension pattern

To add a module, create a `SubjectModule` with `TopicRoute` entries and register it in a `SubjectModuleRegistry`. Keep subject-specific misconceptions and visuals in the module; keep learner state, challenge selection, remediation accounting, and mastery decisions in MPS.
