import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.mpve_narration import build_narration_plan, mix_narration
from scripts.video_explainer import build_storyboard


class MPVENarrationTests(unittest.TestCase):
    def test_narration_plan_matches_arbitrary_storyboard_duration(self):
        storyboard = build_storyboard(
            topic="Hydrostatic Pressure",
            objective="Explain pressure variation with depth.",
            narration="Start with a slab. Derive the pressure difference. Apply the result.",
            mastery_check="Predict the result at double depth.",
            duration=120,
            derived=True,
        )
        turns = build_narration_plan(storyboard)
        self.assertEqual(len(turns), len(storyboard.scenes))
        self.assertEqual(turns[0].start_seconds, 0)
        self.assertEqual(turns[-1].end_seconds, 120)
        self.assertTrue(all(turn.end_seconds > turn.start_seconds for turn in turns))

    def test_mix_narration_builds_duration_aware_ffmpeg_command(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "narrated.mp4"
            completed = type("Completed", (), {})()
            with patch("scripts.mpve_narration.shutil.which", return_value="/usr/bin/ffmpeg"), patch("scripts.mpve_narration.subprocess.run", return_value=completed) as run:
                video = Path(directory) / "video.mp4"
                audio = Path(directory) / "narration.mp3"
                video.write_bytes(b"video")
                audio.write_bytes(b"audio")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"output")
                result = mix_narration(video, audio, output, duration_seconds=120)
                self.assertEqual(result, output.resolve())
                command = run.call_args.args[0]
                self.assertIn("atrim=duration=120", command[command.index("-filter_complex") + 1])


if __name__ == "__main__":
    unittest.main()
