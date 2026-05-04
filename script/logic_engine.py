import sys
import json
import random

def first_principles_logic(formula_or_concept, hobby=None):
    """
    Strips formulas into physical 'Core Truths' and applies a relatability filter if a hobby is provided.
    """
    core_truths = {
        "F=ma": "Push strength depends on weight and desired speed.",
        "E=mc^2": "Energy and matter are two forms of the same thing; a tiny bit of matter is a huge amount of energy.",
        "V=IR": "Electrical pressure (Voltage) equals the flow (Current) times the resistance of the path.",
        "PV=nRT": "Gas pressure and volume are balanced by the amount of gas and its temperature.",
        "a^2 + b^2 = c^2": "The square of the longest side of a right triangle is the sum of the squares of the other two sides.",
        "Torque": "Turning force depends on how hard you push and how far from the pivot you are."
    }
    base_truth = core_truths.get(formula_or_concept, f"Core Truth for '{formula_or_concept}': [Logic to be derived based on physical constraints]")

    if hobby:
        # Simple relatability filter for demonstration
        if hobby.lower() == "gaming":
            return f"{base_truth} (Think of it like: {formula_or_concept} in a game, where {formula_or_concept} is a game mechanic affecting your character's stats or actions.)"
        elif hobby.lower() == "football":
            return f"{base_truth} (Imagine this in football: {formula_or_concept} is like the force a player applies to the ball, influencing its speed and direction.)"
        elif hobby.lower() == "music":
            return f"{base_truth} (In music, {formula_or_concept} could be compared to the rhythm and tempo, where changes in one affect the other.)"
    return base_truth

def generate_mind_map(topic, sections):
    """
    Generates a Mermaid.js mind map for the curriculum.
    """
    mermaid = "mindmap\n"
    mermaid += f"  root(({topic}))\n"
    for section, sub_units in sections.items():
        mermaid += f"    {section}\n"
        for unit in sub_units:
            mermaid += f"      {unit}\n"
    return mermaid

def celebration_function():
    """
    Generates a celebration message with ASCII art or emojis.
    """
    celebrations = [
        "🎉 CONGRATULATIONS! YOU NAILED IT! 🎉",
        "🌟 EXCELLENT WORK! ONWARD AND UPWARD! 🚀",
        "✨ MASTERY ACHIEVED! KEEP UP THE GREAT LEARNING! ✨",
        "🥳 BOOM! ANOTHER SUB-UNIT MASTERED! 🎊"
    ]
    return random.choice(celebrations)

def adapt_narrative(topic, narrative_type):
    """
    Adapts a narrative quest framework to a specific topic.
    This is a placeholder for more sophisticated LLM-driven narrative generation.
    """
    narratives = {
        "Sci-Fi Survival Mission": {
            "hook": "A critical system on your deep-space vessel, the {topic} drive, has failed. You need to calculate the precise {topic} output to prevent a catastrophic system collapse.",
            "teaching": "Solving {topic} problems are your 'repairs' to the failing system."
        },
        "Archeological Mystery": {
            "hook": "You've discovered ancient ruins with advanced {topic} technology. Deciphering the {topic} equations is key to unlocking the next chamber.",
            "teaching": "Mathematical {topic} formulas are 'ancient codes' or 'structural blueprints'."
        },
        "Microscopic Detective": {
            "hook": "A mysterious {topic} anomaly is threatening the biological system. You must identify the {topic} interactions to synthesize a cure.",
            "teaching": "Every sub-unit on {topic} is a 'clue' to finding the cure."
        },
        "Engineering Championship": {
            "hook": "In the Grand Innovation Championship, you must design a {topic}-powered robot. Optimizing the {topic} parameters will secure your victory.",
            "teaching": "Learning {topic} increments are 'upgrades' or 'blueprints' for your project."
        }
    }
    
    selected_narrative = narratives.get(narrative_type, {"hook": "", "teaching": ""})
    
    return {
        "title": narrative_type,
        "hook": selected_narrative["hook"].format(topic=topic),
        "teaching_method": selected_narrative["teaching"].format(topic=topic)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 logic_engine.py <action> <data> [hobby/narrative_type]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "first_principles":
        concept = sys.argv[2]
        hobby = sys.argv[3] if len(sys.argv) > 3 else None
        print(first_principles_logic(concept, hobby))
    elif action == "mind_map":
        try:
            data = json.loads(sys.argv[2])
            print(generate_mind_map(data['topic'], data['sections']))
        except Exception as e:
            print(f"Error generating mind map: {e}")
    elif action == "celebrate":
        print(celebration_function())
    elif action == "adapt_narrative":
        topic = sys.argv[2]
        narrative_type = sys.argv[3]
        print(json.dumps(adapt_narrative(topic, narrative_type)))
