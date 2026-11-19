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
            self.assertTrue(result.recovery_key)
            self.assertTrue(submissions[0]["idempotency_key"])
            self.assertEqual(len(decisions), 1)
            self.assertEqual(len(submissions), 1)
            duplicate = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(duplicate.action, "await_video")
            self.assertEqual(len(submissions), 1)
            orchestrator.handle_video_status(result.recovery_key, {
                "job": {"job_id": "mps-test", "state": "completed"},
                "result": {"artifact": "/tmp/video.mp4", "qa": {"status": "pass"}},
            })
            orchestrator.complete_recovery("buoyancy", success=True, recovery_key=result.recovery_key)
            self.assertEqual(store.load().consecutive_incorrect["buoyancy"], 0)

    def test_missing_submit_adapter_falls_back_to_text(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LearnerStateStore(Path(directory) / "learner.json")
            orchestrator = MPSRecoveryOrchestrator(store, video_decider=lambda _context: True)
            args = dict(concept_id="buoyancy", topic="Floatation", objective="Explain buoyancy", mastery_check="State equilibrium")
            for _ in range(2):
                orchestrator.record_answer(correct=False, **args)
            result = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(result.action, "remediate_text")
            self.assertIn("no MPVE submit adapter", result.message)
            self.assertTrue(result.video_request["idempotency_key"])
            self.assertEqual(store.load().video_jobs, {})

    def test_async_video_failure_returns_to_text_and_retry_reuses_key(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LearnerStateStore(Path(directory) / "learner.json")
            submissions = []
            orchestrator = MPSRecoveryOrchestrator(
                store,
                video_decider=lambda _context: True,
                submit_video=lambda request: submissions.append(request) or {"job_id": f"mps-{len(submissions)}", "state": "queued"},
            )
            args = dict(concept_id="buoyancy", topic="Floatation", objective="Explain buoyancy", mastery_check="State equilibrium", misconception="heavier objects must sink")
            for _ in range(2):
                orchestrator.record_answer(correct=False, **args)
            submitted = orchestrator.record_answer(correct=False, **args)
            failure = orchestrator.handle_video_status(submitted.recovery_key, {
                "job_id": "mps-1", "state": "failed", "error": "temporary renderer failure",
            })
            self.assertEqual(failure.action, "remediate_text")
            self.assertIn("written remediation", failure.message)
            retried = orchestrator.record_answer(correct=False, **args)
            self.assertEqual(retried.action, "video_requested")
            self.assertEqual(len(submissions), 2)
            self.assertEqual(submissions[0]["idempotency_key"], submissions[1]["idempotency_key"])

    def test_video_requires_artifact_before_mastery_check(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LearnerStateStore(Path(directory) / "learner.json")
            orchestrator = MPSRecoveryOrchestrator(
                store,
                video_decider=lambda _context: True,
                submit_video=lambda _request: {"job_id": "mps-test", "state": "queued"},
            )
            args = dict(concept_id="buoyancy", topic="Floatation", objective="Explain buoyancy", mastery_check="State equilibrium")
            for _ in range(2):
                orchestrator.record_answer(correct=False, **args)
            submitted = orchestrator.record_answer(correct=False, **args)
            missing_artifact = orchestrator.handle_video_status(submitted.recovery_key, {
                "job": {"job_id": "mps-test", "state": "completed"},
            })
            self.assertEqual(missing_artifact.action, "remediate_text")
            failed_qa = orchestrator.handle_video_status(submitted.recovery_key, {
                "job": {"job_id": "mps-test", "state": "completed"},
                "result": {"artifact": "/tmp/video.mp4", "qa": {"status": "fail"}},
            })
            self.assertEqual(failed_qa.action, "remediate_text")
            ready = orchestrator.handle_video_status(submitted.recovery_key, {
                "job": {"job_id": "mps-test", "state": "completed"},
                "result": {"artifact": "/tmp/video.mp4", "qa": {"status": "pass"}},
            })
            self.assertEqual(ready.action, "await_mastery_check")
            self.assertEqual(store.load().video_jobs[submitted.recovery_key]["state"], "completed")

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
