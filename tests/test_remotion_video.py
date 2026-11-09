import unittest

from scripts.remotion_video import storyboard_props
from scripts.video_explainer import build_storyboard


class RemotionVideoTests(unittest.TestCase):
    def test_props_preserve_complete_equation_derivation(self):
        storyboard = build_storyboard(
            topic="Floatation",
            objective="Relate buoyant force and weight.",
            narration="A floating body reaches equilibrium.",
            mastery_check="State the equilibrium condition.",
            equations=["F_B = ρfluid g Vdisplaced", "F_B = mg", "ρfluid g Vdisplaced = mg"],
            exam_profile="NEET",
            derived=True,
        )
        props = storyboard_props(storyboard)
        equation_scene = props["scenes"][2]
        self.assertEqual(equation_scene["equations"], [
            "F_B = ρfluid g Vdisplaced",
            "F_B = mg",
            "ρfluid g Vdisplaced = mg",
        ])

    def test_props_preserve_hydrostatic_visual_phases(self):
        storyboard = build_storyboard(
            topic="Hydrostatic Pressure",
            objective="Explain pressure variation with depth.",
            narration="A slab of fluid experiences a pressure difference.",
            mastery_check="Predict pressure at double depth.",
            equations=["ΔP = F/A", "ΔP = ρgh", "P = P₀ + ρgh"],
            duration=30,
            learner_interest="coding and game development",
            analogy_consent=True,
            derived=True,
        )
        props = storyboard_props(storyboard)
        self.assertEqual(props["scenes"][0]["visual"]["kind"], "hydrostatic")
        self.assertEqual(props["scenes"][4]["visual"]["phase"], "4")


if __name__ == "__main__":
    unittest.main()
