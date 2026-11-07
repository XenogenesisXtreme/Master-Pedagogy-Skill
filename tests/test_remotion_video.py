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


if __name__ == "__main__":
    unittest.main()
