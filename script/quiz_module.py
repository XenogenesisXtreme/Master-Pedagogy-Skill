import sys
import random
import json

def generate_quiz(topic, difficulty="normal"):
    """
    Generates a placeholder quiz structure.
    In a real scenario, this would call an LLM or a database.
    """
    quizzes = {
        "Linear Dynamics": [
            {"type": "MCQ", "question": "If mass doubles and force stays the same, what happens to acceleration?", "options": ["Doubles", "Halves", "Stays same"], "answer": "Halves", "hint": "Think about Newton\"s Second Law: F = ma."},
            {"type": "TF", "question": "In a vacuum, a feather and a hammer fall at the same rate.", "answer": "True", "hint": "Gravity acts on all mass equally when air resistance is gone."}
        ]
    }
    return quizzes.get(topic, [{"type": "Conceptual", "question": f"Explain the core truth of {topic}.", "answer": "N/A", "hint": "Focus on the physical intuition."}])

def evaluate_answer(user_answer, correct_answer, hint, consecutive_incorrect=0):
    xp_gained = 0
    support_mode_triggered = False
    message = ""
    animation = ""

    if user_answer.strip().lower() == correct_answer.strip().lower():
        xp_gained = 100
        message = "✨ LEVEL UP! ✨ Mastery confirmed. Unlocking next unit..."
        animation = "[ >>> PROGRESSING >>> ]"
        consecutive_incorrect = 0 # Reset consecutive incorrect on correct answer
    else:
        consecutive_incorrect += 1
        message = "Not quite. Let\"s try a Remedial Loop."
        if consecutive_incorrect >= 2:
            support_mode_triggered = True
            message += "\nEntering Support Mode: Here\'s a simpler, more visual analogy.\n[Placeholder for simpler explanation]"

    return {
        "status": "success" if xp_gained > 0 else "fail",
        "message": message,
        "xp_gained": xp_gained,
        "hint": hint if xp_gained == 0 else None,
        "animation": animation,
        "consecutive_incorrect": consecutive_incorrect,
        "support_mode_triggered": support_mode_triggered
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 quiz_module.py <action> <data>")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "evaluate":
        # Simplified evaluation for CLI demonstration
        user_ans = sys.argv[2]
        correct_ans = sys.argv[3]
        hint = sys.argv[4]
        consecutive_incorrect = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        result = evaluate_answer(user_ans, correct_ans, hint, consecutive_incorrect)
        print(json.dumps(result)) # Output as JSON for easier parsing
    elif action == "generate":
        topic = sys.argv[2]
        quiz = generate_quiz(topic)
        print(json.dumps(quiz)) # Output as JSON
