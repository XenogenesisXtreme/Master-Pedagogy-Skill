import json
import tempfile
import unittest
from pathlib import Path

from scripts.mpve_captions import CaptionWord, write_sidecars
from scripts.mpve_timeline import Timeline, TimelineClip, transition_window
from scripts.mpve_qa import inspect_media


class MPVEContractTests(unittest.TestCase):
    def test_timeline_rounding_and_local_transition_bounds(self):
        clip = TimelineClip("one", 0.0, 1.0, transition_in="fade", transition_out="fade", transition_seconds=0.5)
        timeline = Timeline(fps=24, clips=[clip])
        self.assertEqual(timeline.frame(0.5), 12)
        self.assertEqual(transition_window(clip, 24), {"duration_frames": 24, "fade_in_frames": 12, "fade_out_frames": 12})
        self.assertEqual(timeline.validate(), [])

    def test_hard_cut_has_no_fade(self):
        clip = TimelineClip("one", 0, 2, transition_in="cut", transition_out="none", transition_seconds=0.5)
        self.assertEqual(transition_window(clip, 24)["fade_in_frames"], 0)
        self.assertEqual(transition_window(clip, 24)["fade_out_frames"], 0)

    def test_caption_sidecars_are_valid_and_carry_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_sidecars([CaptionWord("A", 0, 999, True), CaptionWord("minute", 60_000, 61_250)], directory)
            self.assertEqual(result["cue_count"], 2)
            self.assertIn("00:01:00,000", Path(result["srt"]).read_text())
            payload = json.loads(Path(result["json"]).read_text())
            self.assertEqual(len(payload["words"]), 2)

    def test_caption_validation_rejects_backwards_time(self):
        with self.assertRaises(ValueError):
            write_sidecars([CaptionWord("late", 500, 900), CaptionWord("early", 100, 200)], tempfile.mkdtemp())

    def test_missing_media_fails_qa(self):
        result = inspect_media("/tmp/mps-file-that-does-not-exist.mp4")
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
