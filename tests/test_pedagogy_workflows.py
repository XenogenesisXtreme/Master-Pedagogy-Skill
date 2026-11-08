import tempfile
import unittest
from pathlib import Path

from scripts.intervention_orchestrator import MPSRecoveryOrchestrator
from scripts.mps_state import LearnerStateStore
from scripts.pedagogy_modules import default_registry


class PedagogyWorkflowTests(unittest.TestCase):
    def test_fluid_mechanics_module_has_reusable_routes(self):
        registry = default_registry()
        module = registry.select("Physics", "hydrostatic pressure")
        route = module.route_for("hydrostatic pressure")
        self.assertEqual(module.id, "fluid-mechanics")
        self.assertIn("P = P₀ + ρgh", " ".join(route.sequence))
        self.assertIn("derive P = P₀ + ρgh", route.mastery_criteria)
        self.assertIn("NEET", route.exam_applications)
        self.assertGreaterEqual(len(module.topics), 9)

    def test_three_errors_wait_then_mps_approves_one_video(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LearnerStateStore(Path(directory) / "learner.json")
            decisions = []
            submissions = []
            orchestrator = MPSRecoveryOrchestrator(
                store,
                video_decider=lambda context: decisions.append(context) or True,
                submit_video=lambda request: submissions.append(request) or {"job_id": "mps-test", "state": "queued"},
            )
            args = dict(concept_id="buoyancy", topic="Floatation", objective="Explain buoyancy", mastery_check="State equilibrium", misconception="heavier objects must sink")
            self.assertEqual(orchestrator.record_answer(correct=False, **args).action, "remediate_text")
            self.assertEqual(orchestrator.record_answer(correct=False, **args).action, "remediate_text")
            result = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(result.action, "video_requested")
            self.assertEqual(len(decisions), 1)
            self.assertEqual(len(submissions), 1)
            duplicate = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(duplicate.action, "await_video")
            self.assertEqual(len(submissions), 1)
            orchestrator.complete_recovery("buoyancy", success=True, recovery_key=next(iter(store.load().video_jobs)))
            self.assertEqual(store.load().consecutive_incorrect["buoyancy"], 0)

    def test_fhp_cannot_bypass_written_derivation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LearnerStateStore(Path(directory) / "learner.json")
            submitted = []
            orchestrator = MPSRecoveryOrchestrator(store, video_decider=lambda _context: True, submit_video=submitted.append)
            args = dict(concept_id="pressure", topic="Hydrostatic pressure", objective="Derive pressure with depth", mastery_check="State the relation", mode="fhp")
            for _ in range(3):
                result = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(result.action, "continue_fhp_discovery")
            self.assertEqual(submitted, [])

    def test_state_store_round_trips_session_context(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learner.json"
            store = LearnerStateStore(path)
            state = store.load()
            state.current_subject = "Physics"
            state.current_subtopic = "Buoyancy"
            state.record_event("prerequisite_audit", confidence="developing")
            store.save(state)
            restored = store.load()
            self.assertEqual(restored.current_subtopic, "Buoyancy")
            self.assertEqual(restored.events[-1]["event"], "prerequisite_audit")


if __name__ == "__main__":
    unittest.main()
