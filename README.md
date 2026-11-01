# gymrat
An AI-powered app that creates personalized workout plans tailored to your fitness goals, experience, and lifestyle.

Coach Dagzz asks what a personal trainer would ask (goal, experience, days per week, equipment,
injuries, preferences) and uses Groq to write a day-by-day plan with sets, reps, rest, and form tips.

## Run it

```bash
cp .env.example .env        # then paste the Groq API key into .env
uv sync
uv run streamlit run app.py
```

<!-- Open http://localhost:8501. -->

`GROQ_MODEL` is optional and defaults to `openai/gpt-oss-120b`.

## Files

| File | What it does |
|---|---|
| `app.py` | Streamlit UI: the form, loading and error states, plan display, downloads |
| `planner.py` | Prompt design, `generate_plan()` (Groq call with type hints and try/except), parsing, validation, exercise swap |
| `exporters.py` | PDF export (`gymrat-plan.pdf`) |
| `mascot.py` | Loads the Coach Dagzz PNGs in `assets/`: full-body flex plus four moods (ready, thinking, hold on, oops) |

## How the prompt keeps the model honest

- **Rules in priority order** in the system prompt: safety, then equipment, then schedule, then level/goal, then preferences.
- **Custom goals.** Users can type their own goal (e.g. "train for a 5K"). It is fenced as client text and
  comes with guidance for working out what it needs, plus fallbacks for non-fitness or medical goals.
- **Translated inputs.** "Beginner" or "Home dumbbells" alone are vague, so each option expands into concrete
  coaching guidance (rep ranges, set counts, rest, what gear exists and what doesn't).
- **Split suggestion** based on days per week, and the exact number of days the output must contain.
- **Free text is fenced** inside `<client_notes>` and treated as information, not instructions.
- **Structured JSON output** with a fixed schema, so the UI can render tables rather than a wall of text.
- **Checked after the fact.** The parser rejects plans with the wrong number of days, and a keyword check
  catches exercises that need gear the user doesn't have; either triggers one automatic retry.

## Error handling

| Situation | What Coach Dagzz says |
|---|---|
| Missing goal or level | "Hold on, I need to know a bit more about you." |
| No equipment picked | "No days or no gear? Pick at least 1 of each." |
| Missing/bad API key, network, rate limit, retired model | A specific friendly message per case |
| Empty, malformed, or incomplete response | "My notes came back blank/scrambled…", after one automatic retry |
| PDF build fails | "The PDF jammed…" (plan stays on screen) |

## Stretch goals included

- **Regenerate** asks for a fresh variation that avoids the previous exercises.
- **Session state** keeps the last plan across reruns.
- **Download** the plan as a PDF.
- **Swap this exercise** replaces one exercise at a time, keeping equipment and injuries in mind.
