"""Turn a WorkoutPlan into a downloadable PDF."""

from fpdf import FPDF
from fpdf.fonts import FontFace

from mascot import coach_image
from planner import WorkoutPlan

PDF_FILE_NAME = "gymrat-plan.pdf"

# Shown under the app's form and plan, and at the end of the PDF.
DISCLAIMER = (
    "Coach Dagzz is an AI, not a certified trainer or doctor. This plan is general fitness guidance, so consult "
    "a doctor before starting if you have health concerns, or injuries. Stop if you experience pain."
)

# The built-in PDF fonts only cover Latin-1, so swap out common LLM punctuation.
_LATIN1_FIXES = {
    "–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "×": "x", "…": "...", "•": "-", "→": "->", "≤": "<=", "≥": ">=", "−": "-",
    " ": " ", " ": " ", " ": " ",
}

class PDFExportError(Exception):
    """Raised when the PDF can't be built."""

def _clean(text: str) -> str:
    for bad, good in _LATIN1_FIXES.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")

def plan_title(plan: WorkoutPlan) -> str:
    return f"Your {len(plan.days)}-day plan"

def coach_notes(plan: WorkoutPlan) -> list[tuple[str, str]]:
    notes = [
        ("Schedule", plan.schedule),
        ("Warm-up", plan.warm_up),
        ("Progression", plan.progression),
        ("How your limits and preferences were handled", plan.adaptations),
        ("Safety", plan.safety),
    ]
    return [(label, text) for label, text in notes if text]

def plan_to_pdf(plan: WorkoutPlan) -> bytes:
    """Build the PDF. Raises PDFExportError with a friendly message on failure."""
    try:
        pdf = FPDF(format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_title("gymrat workout plan")
        pdf.add_page()

        # Header: logo, app name, title, inputs summary
        try:
            pdf.image(str(coach_image()), x=13, y=13, w=19)  # height follows the image
        except Exception:
            pass  # A missing logo shouldn't block the plan.
        pdf.set_xy(34, 15)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "gymrat")
        pdf.set_y(32)
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 8, _clean(plan_title(plan)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(110, 110, 110)
        subtitle = plan.title + (f"  |  {plan.inputs.summary()}" if plan.inputs else "")
        pdf.multi_cell(0, 5, _clean(subtitle.replace(" · ", ", ")), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # One section per day
        heading = FontFace(emphasis="BOLD", fill_color=(240, 239, 236))
        for day in plan.days:
            minutes = f"  (~{day.duration_minutes} min)" if day.duration_minutes else ""
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, _clean(f"Day {day.day} - {day.name}{minutes}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            with pdf.table(col_widths=(52, 14, 18, 16), headings_style=heading, line_height=6) as table:
                table.row(["Exercise", "Sets", "Reps", "Rest"])
                for ex in day.exercises:
                    name = f"{ex.name}\n{ex.notes}" if ex.notes else ex.name
                    table.row([_clean(name), _clean(ex.sets), _clean(ex.reps), _clean(ex.rest)])
            if day.tip:
                pdf.set_font("Helvetica", "I", 9)
                pdf.multi_cell(0, 5, _clean(f"Coach's tip: {day.tip}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        # Coach's notes at the end
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Coach's notes", new_x="LMARGIN", new_y="NEXT")
        for label, text in coach_notes(plan):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, _clean(label), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, _clean(text), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(110, 110, 110)
        pdf.multi_cell(0, 4, _clean(DISCLAIMER), new_x="LMARGIN", new_y="NEXT")

        return bytes(pdf.output())
    except Exception as exc:
        raise PDFExportError("The PDF jammed. Your plan's still on screen, so copy it for now.") from exc
