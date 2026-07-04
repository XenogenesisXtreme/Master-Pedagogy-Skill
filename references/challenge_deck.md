# The Challenge Deck

Agent C picks from these 7 formats after every sub-unit, using `scripts/quiz_module.py`'s `pick_next_format()` to avoid running the same one twice in a row (and to avoid Boss Battle showing up anywhere but a Level Up moment). Each entry gives the structure, what "correct" means, and how to render it in both modes.

Rendering note: "Rich Mode" = `visualize:show_widget` available (load the `interactive` module first for these). "Text Mode" = plain chat text. Both are described for each format — never skip Text Mode just because Rich Mode is available; always have the fallback ready.

---

## 1. Speed Round
**Structure**: 3 rapid-fire MCQs on the same sub-unit, meant to feel quick, not deep. Good right after a concept is first introduced, to check surface recognition before going deeper.
**Correct**: 3/3 needed to pass clean; 2/3 triggers a light "one more to lock it in" follow-up rather than a full Remedial Loop.
**Rich Mode**: A widget with a visible (fake but motivating) timer, big tap targets, immediate green/red flash per answer.
**Text Mode**: Three questions posted together, lettered choices, "answer all three in one message: A/B/C style."

## 2. Build-It
**Structure**: Give the learner a partially-built solution (equation, proof step, process) with blanks; they fill the blanks by dragging terms (Rich Mode) or naming them (Text Mode).
**Correct**: All blanks right = pass. One wrong blank = point at just that blank for a mini-Remedial moment rather than redoing the whole thing.
**Rich Mode**: Drag-and-drop widget with word/term tiles.
**Text Mode**: Numbered blanks, learner replies with "1: ___, 2: ___" etc.

## 3. Debug-It
**Structure**: Show a fully worked (but subtly wrong) solution to a problem. The learner has to find and explain the error — this tests conceptual understanding harder than "solve it yourself" because they have to recognize wrongness, not just pattern-match.
**Correct**: Identifies the specific error AND why it's wrong (partial credit if they spot it but explain it shakily → quick clarifying follow-up, not a full loop).
**Rich Mode**: Worked solution rendered as a widget, clickable line-by-line to "flag" the error.
**Text Mode**: Numbered lines of the worked solution, learner names the line + explains.

## 4. Prediction Market
**Structure**: Before showing the answer to a conceptual question, ask the learner to predict the outcome first ("will X go up, down, or stay the same if we double Y?"), then reveal.
**Correct**: The prediction matching + a correct reason. A right guess with a wrong reason is treated as incorrect (they need the mechanism, not the lucky guess) — flag this gently, it's a common false positive.
**Rich Mode**: A simple slider/toggle for the prediction, then an animated reveal (e.g. a graph line moving to the real answer).
**Text Mode**: Ask for the prediction in one message, hold the reveal for the next.

## 5. Scenario MCQ
**Structure**: A short real-world scenario (2-3 sentences) ending in an MCQ — tests application, not recall. This is the default "standard quiz" format when nothing more specific fits.
**Correct**: Standard single right answer among 4 options, with plausible distractors that represent common misconceptions (not throwaway wrong answers).
**Rich Mode**: Clickable answer cards.
**Text Mode**: Lettered options, reply with the letter.

## 6. True/False Gauntlet
**Structure**: A rapid series of 4-5 True/False statements about the sub-unit, including at least one deliberately tricky "true-sounding false" statement to catch surface-level pattern matching.
**Correct**: 4/5 or better to pass; any miss on the "tricky" statement specifically gets called out and explained regardless of overall pass, since that's the one testing real understanding.
**Rich Mode**: Toggle switches or True/False buttons per statement, all visible at once.
**Text Mode**: Numbered list, learner replies T/F per number.

## 7. Boss Battle
**Structure**: Reserved for Level Up moments (every 500 XP), never a regular sub-unit check. A multi-step, high-difficulty, real-world application problem themed to the active Narrative Quest, combining 2+ concepts from the levels just completed.
**Correct**: Full multi-step solution; partial credit is real here — a mostly-right approach with one arithmetic slip is a "battle won, took some damage" outcome (small XP penalty, not a full Remedial Loop), while a wrong approach is a genuine loss that triggers a proper multi-part remedial pass before retrying.
**Rich Mode**: The most elaborate widget of the set — a themed scenario UI (ship console, vault panel, judge's scorecard) with multiple input steps and a dramatic resolve animation.
**Text Mode**: Presented as a multi-part narrative scene with clearly numbered sub-questions; resolve with a written "battle report" summarizing what worked and what didn't.

---

## Anti-Repeat Rule

Never run the same format (other than Boss Battle, which only ever appears at Level Up) twice in a row. `scripts/quiz_module.py`'s `pick_next_format()` handles this — pass it the history of recent formats and it returns a valid next pick. If calling it isn't practical in the moment, apply the same rule by eye: check what the last format was and pick a different one.

Match format to content, not just rotation for its own sake — Debug-It works best once there's a worked example worth breaking; Prediction Market works best on concepts with a clear directional relationship (more of X → more/less of Y); Build-It works best on multi-step derivations or processes.
