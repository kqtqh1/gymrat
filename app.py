"""gymrat: a Streamlit workout plan generator with an AI coach dagzz."""

from html import escape
import streamlit as st
from exporters import DISCLAIMER, PDF_FILE_NAME, PDFExportError, coach_notes, plan_to_pdf, plan_title
from mascot import Mood, coach_image, coach_tag
from planner import (
    EQUIPMENT_OPTIONS,
    EXPERIENCE_LEVELS,
    GOALS,
    COACH_NAME,
    MAX_TEXT_LENGTH,
    EmptyResponseError,
    InvalidInputError,
    PlanError,
    PlanInputs,
    WorkoutPlan,
    generate_plan,
    swap_exercise,
    validate_inputs,
)

st.set_page_config(page_title="gymrat", page_icon=str(coach_image()), layout="wide")

FLEX_HEIGHT = 110

st.markdown(
    """
<style>
.coach{display:flex;align-items:center;gap:12px;margin:0 0 12px}
.bub{position:relative;flex:1;background:rgba(128,128,128,.08);border:0.5px solid rgba(128,128,128,.4);
  border-radius:12px;padding:10px 14px;font-size:15px;line-height:1.45}
.bub:before{content:"";position:absolute;left:-6px;top:50%;margin-top:-5px;width:10px;height:10px;
  background:inherit;border-left:0.5px solid rgba(128,128,128,.4);border-bottom:0.5px solid rgba(128,128,128,.4);
  transform:rotate(45deg)}
.bub.sm{font-size:14px;padding:8px 12px}
.bub.warning{background:#FDF1D8;border-color:#E9B949;color:#734500}
.bub.danger{background:#FBE4E4;border-color:#E39A9A;color:#8E2626}
.bub.success{background:#E3F4E8;border-color:#7CC395;color:#1F5C33}
.brand{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.brand b{font-size:26px;font-weight:600}
.fh{font-size:13px;opacity:.6;margin:4px 0 2px}
.ticks{display:flex;justify-content:space-between;font-size:12px;opacity:.55;margin:-14px 0 0;padding:0 6px}
[data-testid="stSliderTickBar"]{display:none}
[data-testid="stSliderThumbValue"]{color:#2B2236 !important;font-weight:600}
hr.sec{border:0;border-top:1px solid rgba(128,128,128,.25);margin:0 !important}
/* Primary button stays dark; yellow is the accent everywhere else */
button[kind="primary"]{background:#151515 !important;border-color:#151515 !important;font-weight:600}
button[kind="primary"]:hover{background:#2B2236 !important;border-color:#2B2236 !important}
button[kind="primary"],button[kind="primary"] *{color:#FFFFFF !important}
button[data-variant][aria-pressed="true"]{
  background:#FFE9A8 !important;border-color:#E0A800 !important;color:#2B2236 !important}
button[data-variant][aria-pressed="true"] *{color:#2B2236 !important}
.plan-title{font-size:22px;font-weight:600;line-height:1.3}
.plan-meta{font-size:13px;opacity:.6;line-height:1.4}
.exname{line-height:1.35}
.th{font-size:13px;opacity:.6}
.exn{font-size:12px;opacity:.6;line-height:1.35;margin-top:2px}
.notes svg{vertical-align:-3px;margin-right:6px}
.tip{display:flex;align-items:center;gap:8px;font-size:14px;opacity:.85;margin-top:6px}
.notes{background:rgba(128,128,128,.08);border-radius:8px;padding:12px 14px;font-size:14px;line-height:1.5;margin-top:8px}
.notes p{margin:0 0 6px}
.notes p:last-child{margin:0}
.center-cap{text-align:center;font-size:13px;opacity:.6;margin:-6px 0 18px}
/* Header sits near the top instead of under Streamlit's default padding */
[data-testid="stMainBlockContainer"]{padding-top:1rem}
[data-testid="stHeader"]{background:transparent}
/* Plan panel: same height as the form column, pinned top, scrolling body */
.st-key-plan_panel{border:1px solid rgba(128,128,128,.3);border-radius:12px;padding:16px;flex-wrap:nowrap}
.st-key-plan_body{padding-right:4px}
@media (min-width:640px){
  [data-testid="stColumn"]:has(.st-key-plan_panel){position:relative}
  .st-key-plan_panel{position:absolute;inset:0}
  [data-testid="stLayoutWrapper"]:has(> .st-key-plan_body){flex:1 1 0;min-height:0}
  .st-key-plan_body{height:100%;overflow-y:auto;flex-wrap:nowrap}
}
/* Header: the coach's flat bottom edge sits on the form's top border, so he peeks over it */
.hero{display:flex;align-items:flex-end;gap:14px;margin-bottom:-1px}
.hero-text{flex:1;margin-bottom:22px}
.empty{height:100%;min-height:320px;display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;gap:10px;padding:40px 24px}
.empty b{font-size:17px}
.empty p{font-size:14px;opacity:.65;max-width:380px;margin:0}
.ghost{width:100%;max-width:380px;display:flex;flex-direction:column;gap:8px;margin-top:8px}
.ghost div{height:34px;border-radius:8px;background:rgba(128,128,128,.1);font-size:13px;opacity:.6;
  display:flex;align-items:center;padding:0 12px}
/* Plan panel while generating */
.spin{width:44px;height:44px;border-radius:50%;border:4px solid rgba(128,128,128,.2);border-top-color:#FFC93C;
  animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading .ghost div{background:linear-gradient(90deg,rgba(128,128,128,.08) 25%,rgba(128,128,128,.22) 50%,
  rgba(128,128,128,.08) 75%);background-size:200% 100%;animation:shimmer 1.4s linear infinite}
@keyframes shimmer{from{background-position:200% 0}to{background-position:-200% 0}}
@media (prefers-reduced-motion:reduce){.spin,.loading .ghost div{animation:none}}
/* Hide the previous plan (left over from the last run) behind the loader */
.st-key-plan_body:has(.loading) > :not(:has(.loading)){display:none}
.disclaimer{text-align:center;font-size:12px !important;opacity:.6;line-height:1.5 !important;max-width:760px;margin:4px auto 0 !important}
</style>
""",
    unsafe_allow_html=True,
)

INFO_ICON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v4h1"/></svg>'
)

SECTION_BREAK = '<hr class="sec">'

EMPTY_PLAN = (
    f'<div class="empty">'
    "<b>No plan yet</b>"
    "<p>Fill in the form and hit <b>Generate plan</b>. Your week shows up here: each training day "
    "with exercises, sets, reps and rest, plus a PDF you can take to the gym.</p>"
    '<div class="ghost"></div></div>'
)

LOADING_PLAN = (
    '<div class="empty loading"><div class="spin" role="status" aria-label="Generating your plan"></div>'
    "<b>Building your plan…</b>"
    "<p>Picking exercises that fit your goal, gear and limits. This takes a few seconds.</p>"
    '<div class="ghost"><div></div><div></div><div></div></div></div>'
)

BUBBLE_TONE: dict[Mood, str] = {"ready": "", "thinking": "", "hold_on": "warning", "oops": "danger"}

def coach_says(message: str, mood: Mood = "ready", size: int = 56, tone: str | None = None) -> str:
    """HTML for the coach with a speech bubble."""
    tone = BUBBLE_TONE[mood] if tone is None else tone
    small = " sm" if size < 80 else ""
    return (
        f'<div class="coach">{coach_tag(size)}'
        f'<div class="bub{small} {tone}">{escape(message)}</div></div>'
    )

WELCOME = (
    f"Hey, I'm {COACH_NAME}. Tell me about your goals, your current lifestyle, and what you're hoping to achieve, "
    "and I'll create a personalized, realistic, and easy-to-follow plan to help you get there"
)
PLAN_READY = "Your plan is all set! All you have to do is show up, give it your best, and let me help you stay on track."

def header_html(message: str, mood: Mood | None = None, tone: str = "") -> str:
    """The page header: flexing coach plus a bubble that carries the current status."""
    return (
        '<div class="hero">'
        f'{coach_tag(FLEX_HEIGHT, mood, f"{COACH_NAME}, a rat trainer doing a double-bicep flex")}'
        '<div class="hero-text"><div class="brand"><b>gymrat</b></div>'
        f'<div class="bub {tone}">{escape(message)}</div></div></div>'
    )

def error_mood(error: Exception) -> tuple[Mood, str]:
    """Which face and bubble color each failure gets (matches the wireframe states)."""
    if isinstance(error, (InvalidInputError, EmptyResponseError)):
        return "hold_on", "warning"
    if isinstance(error, PDFExportError):
        return "oops", "warning"
    return "oops", "danger"

def show_error(slot, error: Exception) -> None:
    mood, tone = error_mood(error)
    slot.markdown(coach_says(str(error), mood, tone=tone), unsafe_allow_html=True)


def on_equipment_change() -> None:
    """'No equipment' can't be combined with gear, so whichever was picked last wins."""
    # The key can be missing if Streamlit dropped the widget's state (e.g. after a hot reload).
    picked = st.session_state.get("equipment") or []
    previous = st.session_state.get("equipment_prev", [])
    if "No equipment" in picked and len(picked) > 1:
        picked = ["No equipment"] if "No equipment" not in previous else [p for p in picked if p != "No equipment"]
    st.session_state.equipment = picked
    st.session_state.equipment_prev = picked

def store_plan(plan: WorkoutPlan) -> None:
    st.session_state.plan = plan
    st.session_state.plan_error = None
    try:
        st.session_state.pdf_bytes = plan_to_pdf(plan)
        st.session_state.pdf_error = None
    except PDFExportError as exc:
        st.session_state.pdf_bytes = None
        st.session_state.pdf_error = exc

def run_generation(inputs: PlanInputs, slot, panel, avoid: list[str] | None = None) -> None:
    """Show the loading state (header and plan panel), call the model, and store either the plan or the error."""
    loading = "Shaking things up. New exercises coming…" if avoid else "Counting reps and checking your limits…"
    slot.markdown(header_html(loading, "thinking"), unsafe_allow_html=True)
    loader = panel.empty()
    loader.markdown(LOADING_PLAN, unsafe_allow_html=True)
    try:
        plan = generate_plan(
            goal=inputs.goal,
            experience=inputs.experience,
            days_per_week=inputs.days_per_week,
            equipment=inputs.equipment,
            other_equipment=inputs.other_equipment,
            limitations=inputs.limitations,
            preferences=inputs.preferences,
            avoid=avoid,
        )
    except PlanError as exc:
        st.session_state.plan_error = exc
    except Exception:
        st.session_state.plan_error = PlanError("Something unexpected tripped me up. Try again in a moment.")
    else:
        store_plan(plan)
    loader.empty()

for key, default in {
    "plan": None,
    "plan_error": None,
    "form_error": None,
    "pdf_bytes": None,
    "pdf_error": None,
    "swap_error": None,
    "equipment": [],
    "equipment_prev": [],
}.items():
    st.session_state.setdefault(key, default)

# ---------- Header ----------

header = st.empty()

# ---------- Form (left part) and plan (right prt) ----------

form_col, plan_col = st.columns([2, 3], gap="large")

with form_col:
    with st.container(border=True):
        # st.markdown('<p class="fh">About you</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            goal = st.selectbox(
                "Fitness goal",
                GOALS,
                index=None,
                placeholder="Choose your goal",
                key="goal",
            )
            # st.caption("Pick the one that matters most. We'll chase the rest later.")
        with col2:
            experience = st.selectbox(
                "Experience level", EXPERIENCE_LEVELS, index=None, placeholder="Choose your level", key="experience"
            )
            # st.caption("Be honest. I won't tell the other rats.")

        st.markdown(SECTION_BREAK, unsafe_allow_html=True)
        # st.markdown('<p class="fh">Your schedule and gear</p>', unsafe_allow_html=True)
        days_value = st.session_state.get("days", 1)
        label_col, value_col = st.columns([4, 1])
        label_col.markdown("Days available per week")
        value_col.markdown(
            f'<div style="text-align:right;font-weight:600">{days_value} {"day" if days_value == 1 else "days"}</div>',
            unsafe_allow_html=True,
        )
        days = st.slider("Days available per week", 1, 7, 1, step=1, key="days", label_visibility="collapsed")
        st.markdown(
            '<div class="ticks">' + "".join(f"<span>{n}</span>" for n in range(1, 8)) + "</div>",
            unsafe_allow_html=True,
        )
        equipment = st.pills(
            "Equipment access (pick all that apply)",
            EQUIPMENT_OPTIONS,
            selection_mode="multi",
            key="equipment",
            on_change=on_equipment_change,
        )
        other_equipment = st.text_input(
            "Other equipment (optional)",
            max_chars=MAX_TEXT_LENGTH,
            placeholder="Resistance bands, pull-up bar",
            key="other_equipment",
        )
        # st.caption("Got gear that's not listed? Add it here.")

        st.markdown(SECTION_BREAK, unsafe_allow_html=True)
        # st.markdown('<p class="fh">Limits and preferences</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            limitations = st.text_area(
                "Injuries or limitations (optional)",
                max_chars=MAX_TEXT_LENGTH,
                placeholder="Bad knees, no overhead pressing",
                height=100,
                key="limitations",
            )
            # st.caption("Tell me what hurts. I'll work around it.")
        with col2:
            preferences = st.text_area(
                "Anything else? (optional)",
                max_chars=MAX_TEXT_LENGTH,
                placeholder="30 minutes per session, I hate burpees",
                height=100,
                key="preferences",
            )
            # st.caption("Time limits, likes, dislikes.")

    form_inputs = PlanInputs(
        goal=(goal or "").strip(),
        experience=experience or "",
        days_per_week=int(days),
        equipment=list(equipment or []),
        other_equipment=other_equipment,
        limitations=limitations,
        preferences=preferences,
    )

    generate = st.button("Generate plan", type="primary", icon=":material/bolt:", width="stretch")
    # st.markdown(f'<p class="center-cap">{COACH_NAME} will build it in a few seconds.</p>', unsafe_allow_html=True)

    start_generation = False
    if generate:
        st.session_state.swap_error = None
        try:
            validate_inputs(form_inputs)
        except InvalidInputError as exc:
            st.session_state.form_error = exc
        else:
            st.session_state.form_error = None
            start_generation = True

# ---------- Plan output ----------

# The panel is stretched to the form's height by CSS. The top part stays put; only the body scrolls.
with plan_col, st.container(key="plan_panel"):
    top = st.container()
    body = st.container(key="plan_body")

with top:
    if start_generation:
        run_generation(form_inputs, header, body)

    plan: WorkoutPlan | None = st.session_state.plan
    if plan:
        title_col, actions_col = st.columns([1, 1], vertical_alignment="center")
        with title_col:
            meta = plan.inputs.summary() if plan.inputs else ""
            st.markdown(
                f'<div class="plan-title">{escape(plan_title(plan))}</div>'
                f'<div class="plan-meta">{escape(plan.title)} · {escape(meta)}</div>',
                unsafe_allow_html=True,
            )
        with actions_col:
            regen_col, pdf_col = st.columns(2)
            regenerate = regen_col.button("Regenerate", icon=":material/refresh:", width="stretch", help="Same inputs, different exercises")
            if st.session_state.pdf_bytes:
                pdf_col.download_button("Download PDF", st.session_state.pdf_bytes, file_name=PDF_FILE_NAME, mime="application/pdf", icon=":material/download:", width="stretch")

        if st.session_state.pdf_error:
            show_error(st.empty(), st.session_state.pdf_error)

        if regenerate and plan.inputs:
            st.session_state.swap_error = None
            st.session_state.form_error = None
            run_generation(plan.inputs, header, body, avoid=plan.exercise_names())
            st.rerun()

with body:
    if not plan:
        st.markdown(EMPTY_PLAN, unsafe_allow_html=True)
    else:
        for d_index, day in enumerate(plan.days):
            minutes = f" · ~{day.duration_minutes} min" if day.duration_minutes else ""
            with st.expander(f"**Day {day.day} · {day.name}**{minutes}", expanded=d_index == 0):
                swap_slot = st.empty()
                swap_error = st.session_state.swap_error
                if swap_error and swap_error[0] == d_index:
                    show_error(swap_slot, swap_error[1])

                widths = [5, 1.3, 1.6, 1.6, 0.9]
                for col, label in zip(st.columns(widths), ["Exercise", "Sets", "Reps", "Rest", ""]):
                    col.markdown(f'<span class="th">{label}</span>', unsafe_allow_html=True)

                for e_index, ex in enumerate(day.exercises):
                    c_name, c_sets, c_reps, c_rest, c_swap = st.columns(widths, vertical_alignment="center")
                    notes = f'<div class="exn">{escape(ex.notes)}</div>' if ex.notes else ""
                    c_name.markdown(f'<div class="exname">{escape(ex.name)}</div>{notes}', unsafe_allow_html=True)
                    for col, value in [(c_sets, ex.sets), (c_reps, ex.reps), (c_rest, ex.rest)]:
                        col.markdown(f"<div>{escape(value)}</div>", unsafe_allow_html=True)
                    if c_swap.button("", icon=":material/swap_horiz:", key=f"swap-{d_index}-{e_index}",
                                     type="tertiary", help=f"Swap {ex.name} for something else"):
                        swap_slot.markdown(coach_says(f"Finding a swap for {ex.name}…", "thinking", size=40),
                                           unsafe_allow_html=True)
                        try:
                            day.exercises[e_index] = swap_exercise(plan, d_index, e_index)
                        except PlanError as exc:
                            st.session_state.swap_error = (d_index, exc)
                        else:
                            st.session_state.swap_error = None
                            store_plan(plan)
                        st.rerun()

                if day.tip:
                    st.markdown(
                        f'<div class="tip">{coach_tag(30)}<span><b>Coach\'s tip:</b> '
                        f"{escape(day.tip)}</span></div>",
                        unsafe_allow_html=True,
                    )

        notes_html = "".join(f"<p><b>{escape(label)}:</b> {escape(text)}</p>" for label, text in coach_notes(plan))
        if notes_html:
            st.markdown(
                f'<div class="notes"><p style="font-weight:600">{INFO_ICON}Coach\'s notes</p>{notes_html}</div>',
                unsafe_allow_html=True,
            )

st.markdown(f'<p class="disclaimer">{escape(DISCLAIMER)}</p>', unsafe_allow_html=True)

# ---------- Header status ----------

# Newest problem first: a form mistake, then a failed generation, then a finished plan.
status_error = st.session_state.form_error or st.session_state.plan_error
if status_error:
    mood, tone = error_mood(status_error)
    header.markdown(header_html(str(status_error), mood, tone), unsafe_allow_html=True)
elif st.session_state.plan:
    header.markdown(header_html(PLAN_READY, "ready", "success"), unsafe_allow_html=True)
else:
    header.markdown(header_html(WELCOME), unsafe_allow_html=True)
