#!/usr/bin/env python3
"""Reusable subject-module contracts for the Master Pedagogy Skill."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class TopicRoute:
    topic: str
    prerequisites: tuple[str, ...]
    sequence: tuple[str, ...]
    discovery_prompts: tuple[str, ...]
    visual_formats: tuple[str, ...]
    misconceptions: tuple[str, ...]
    mastery_criteria: tuple[str, ...]
    remediation: tuple[str, ...]
    exam_applications: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SubjectModule:
    id: str
    name: str
    subject: str
    description: str
    topics: dict[str, TopicRoute]
    supported_profiles: tuple[str, ...]

    def route_for(self, topic: str) -> TopicRoute:
        key = topic.strip().lower()
        if key in self.topics:
            return self.topics[key]
        for name, route in self.topics.items():
            if name in key or key in name:
                return route
        raise KeyError(f"No route for topic {topic!r} in module {self.id!r}")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["topics"] = {key: route.to_dict() for key, route in self.topics.items()}
        return data


class SubjectModuleRegistry:
    def __init__(self, modules: Iterable[SubjectModule] = ()):
        self._modules = {module.id: module for module in modules}

    def register(self, module: SubjectModule) -> None:
        if not module.id.strip():
            raise ValueError("module id is required")
        self._modules[module.id] = module

    def get(self, module_id: str) -> SubjectModule:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise KeyError(f"Unknown subject module {module_id!r}") from exc

    def select(self, subject: str, topic: str = "") -> SubjectModule:
        query = f"{subject} {topic}".lower()
        for module in self._modules.values():
            if module.subject.lower() in query or module.name.lower() in query:
                return module
        raise KeyError(f"No subject module matches subject={subject!r}, topic={topic!r}")

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._modules))


def _route(topic: str, prerequisites: tuple[str, ...], sequence: tuple[str, ...], discovery: tuple[str, ...], visuals: tuple[str, ...], misconceptions: tuple[str, ...], mastery: tuple[str, ...], remediation: tuple[str, ...], *, neet: tuple[str, ...] = (), nsejs: tuple[str, ...] = ()) -> TopicRoute:
    return TopicRoute(topic, prerequisites, sequence, discovery, visuals, misconceptions, mastery, remediation, {"NEET": neet, "NSEJS": nsejs})


def fluid_mechanics_module() -> SubjectModule:
    """Return the reusable Fluid Mechanics module, not a one-topic tutor."""
    common = ("force and area", "density and units", "vectors and equilibrium")
    hydrostatic = _route(
        "hydrostatic pressure", common,
        ("audit force, area, and pressure", "prediction: compare pressure at two depths", "observe depth dependence", "derive P = P₀ + ρgh", "interpret every term", "test direct and inverse proportionality", "transfer check", "mastery gate", "remediate with a fresh example", "offer next route"),
        ("What changes when the same fluid column gets deeper?", "Would pressure be different sideways or only at a point?"),
        ("depth-pressure graph", "fluid column diagram", "textbook equation derivation"),
        ("pressure depends only on force, not area", "pressure is a vector", "atmospheric pressure disappears below a surface"),
        ("derive P = P₀ + ρgh", "predict how pressure changes when depth or density changes", "explain assumptions and limits"),
        ("re-audit force/area", "use a two-depth numerical comparison", "return to the prediction before re-deriving"),
        neet=("NCERT pressure-depth relation", "single-best-answer conceptual comparison"),
        nsejs=("observation-based pressure experiment", "diagram and evidence interpretation"),
    )
    buoyancy = _route(
        "buoyancy", common + ("free-body diagrams",),
        ("audit displaced volume", "predict sink, float, or suspend", "compare pressure on lower and upper faces", "derive buoyant force", "connect equilibrium to displaced fluid", "transfer check", "mastery gate"),
        ("Why can an object heavier than some fluid still float?", "What changes if only displaced volume changes?"),
        ("free-body diagram", "immersed-volume animation", "aligned force equations"),
        ("heavier always sinks", "buoyant force equals object weight in every case", "displaced volume equals object volume when partially submerged"),
        ("identify the pressure imbalance", "state Fᵦ = ρfluid g Vdisplaced", "classify floating, suspended, and sinking cases"),
        ("rebuild the force diagram", "compare two displaced volumes", "use a limiting case of full submersion"),
        neet=("Archimedes principle and equilibrium cases",),
        nsejs=("water-displacement observation and classification",),
    )
    routes = {
        "pressure": _route("pressure", ("force and area", "units"), ("audit force and area", "predict pressure change", "define pressure", "derive p = F/A", "transfer check", "mastery gate"), ("Which surface feels greater pressure?",), ("force-area diagram", "comparison table"), ("pressure is force itself", "larger area always means larger pressure"), ("use p = F/A correctly", "explain inverse area dependence"), ("change one variable at a time",), neet=("definition and distractor analysis",), nsejs=("measurement interpretation",)),
        "hydrostatic pressure": hydrostatic,
        "pascal's law": _route("Pascal's law", ("pressure", "force transmission"), ("audit enclosed-fluid assumptions", "predict pressure transmission", "state Pascal's law", "apply hydraulic advantage", "transfer check", "mastery gate"), ("Why does pressure transmit through a confined fluid?",), ("hydraulic press diagram", "force-area ratio"), ("force is transmitted unchanged", "output force is always equal to input force"), ("relate equal pressure to different areas",), ("label input/output areas",), neet=("hydraulic machines",), nsejs=("simple hydraulic observation",)),
        "buoyancy": buoyancy,
        "archimedes' principle": buoyancy,
        "continuity equation": _route("Continuity equation", ("density", "area", "flow rate"), ("audit steady-flow assumptions", "predict speed in a narrow section", "define volume flow", "derive A₁v₁ = A₂v₂", "transfer check", "mastery gate"), ("Where must fluid move faster?",), ("pipe constriction animation", "area-speed graph"), ("pressure and speed are the same idea", "mass conservation is optional"), ("use conservation of mass", "predict qualitative speed change"), ("compare wide and narrow sections",), neet=("qualitative flow comparison",), nsejs=("flow-rate evidence",)),
        "bernoulli's principle": _route("Bernoulli's principle", ("continuity", "energy", "pressure"), ("audit energy terms", "predict pressure in faster flow", "state assumptions", "derive energy relation", "interpret terms", "transfer check", "mastery gate"), ("Why can faster flow correspond to lower pressure?",), ("streamline diagram", "energy bar chart", "equation reveal"), ("Bernoulli applies to every flow", "speed alone determines pressure"), ("identify assumptions", "compare pressure, kinetic, and potential terms"), ("return to energy conservation",), neet=("qualitative application",), nsejs=("flow observation",)),
        "viscosity": _route("Viscosity", ("friction", "velocity gradient"), ("audit internal friction", "predict resistance change", "define viscosity", "connect shear and gradient", "transfer check", "mastery gate"), ("Why do honey and water flow differently?",), ("velocity-profile graph", "layered flow"), ("viscosity is density", "all fluids have the same resistance"), ("interpret a velocity gradient",), ("compare two flow profiles",), neet=("fluid-property comparison",), nsejs=("observation classification",)),
        "surface tension": _route("Surface tension", ("molecular attraction", "energy"), ("audit cohesive forces", "predict droplet shape", "model surface energy", "explain pressure effects", "transfer check", "mastery gate"), ("Why does a small droplet tend toward a sphere?",), ("molecular force sketch", "surface-energy diagram"), ("surface tension is a skin", "only gravity shapes droplets"), ("connect cohesion to surface energy",), ("compare soap and water",), neet=("capillarity and droplets",), nsejs=("surface observation",)),
        "fluid flow applications": _route("Fluid flow applications", ("continuity", "Bernoulli", "pressure"), ("audit model selection", "predict application behavior", "select governing relation", "solve a constrained case", "check assumptions", "mastery gate"), ("Which principle explains the observed device?",), ("annotated device diagram", "process animation"), ("use a memorized formula without assumptions",), ("name principle and assumptions",), ("separate model selection from algebra",), neet=("application MCQ",), nsejs=("device evidence interpretation",)),
    }
    return SubjectModule("fluid-mechanics", "Fluid Mechanics", "Physics", "A reusable physical-intuition, derivation, visualization, and application module for fluids.", routes, ("General / Conceptual Learning", "NEET", "NSEJS", "JEE"))


def default_registry() -> SubjectModuleRegistry:
    return SubjectModuleRegistry((fluid_mechanics_module(),))
