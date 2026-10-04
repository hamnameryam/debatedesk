import html
import os

import streamlit as st

from agent import DebateError, run_debate

st.set_page_config(page_title="Multi-Agent Debate", page_icon="🗣️", layout="centered")

MIN_TOPIC_CHARS = 3

STYLE = """
<style>
/* ---------- Hero ---------- */
.hero {
    background: linear-gradient(120deg, #4f46e5 0%, #9333ea 55%, #ec4899 100%);
    border-radius: 18px;
    padding: 1.8rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
}
.hero-title { color: #fff; font-size: 2.1rem; font-weight: 800; line-height: 1.2; }
.hero-sub   { color: rgba(255,255,255,.92); font-size: 1.02rem; margin-top: .4rem; }

/* ---------- Form ---------- */
[data-testid="stForm"] {
    border: 1px solid rgba(108, 92, 231, .35);
    border-radius: 16px;
    padding: 1.3rem;
    background: linear-gradient(135deg, rgba(108,92,231,.08), rgba(236,72,153,.07));
}
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #6C5CE7, #EC4899);
    color: #fff;
    border: 0;
    font-weight: 700;
    border-radius: 10px;
}
[data-testid="stFormSubmitButton"] button:hover { filter: brightness(1.1); color: #fff; }

/* ---------- Topic ---------- */
.topic-box {
    border-radius: 14px;
    padding: .9rem 1.1rem;
    margin: 1.2rem 0 .4rem;
    background: rgba(108, 92, 231, .10);
    border: 1px solid rgba(108, 92, 231, .35);
}
.topic-label { font-size: .72rem; font-weight: 800; letter-spacing: .12em; color: #6C5CE7; }
.topic-text  { font-size: 1.15rem; font-weight: 600; margin-top: .15rem; }

/* ---------- Round badge ---------- */
.round-badge {
    display: inline-block;
    margin: 1.4rem 0 .6rem;
    padding: .3rem 1rem;
    border-radius: 999px;
    color: #fff;
    font-weight: 800;
    font-size: .85rem;
    letter-spacing: .1em;
    background: linear-gradient(90deg, #4f46e5, #9333ea);
}

/* ---------- Argument cards ---------- */
[class*="st-key-card_for_"], [class*="st-key-card_against_"], [class*="st-key-card_verdict"] {
    border-radius: 14px;
    padding: 1rem 1.3rem 1.1rem;
}
[class*="st-key-card_for_"]     { background: rgba(22, 163, 74, .09);  border-left: 6px solid #16a34a; }
[class*="st-key-card_against_"] { background: rgba(225, 29, 72, .08);  border-left: 6px solid #e11d48; }
[class*="st-key-card_verdict"]  { background: rgba(245, 158, 11, .10); border: 2px solid #f59e0b; }

/* tame big markdown headings the model writes inside arguments */
[class*="st-key-card_"] h1, [class*="st-key-card_"] h2,
[class*="st-key-card_"] h3, [class*="st-key-card_"] h4 {
    font-size: 1.05rem !important;
    padding: 0;
    margin: .8rem 0 .3rem;
}
[class*="st-key-card_"] hr { margin: .9rem 0; }

.card-head { display: flex; align-items: center; gap: .7rem; }
.pill {
    padding: .2rem .75rem;
    border-radius: 999px;
    color: #fff;
    font-weight: 800;
    font-size: .78rem;
    letter-spacing: .08em;
}
.pill-for     { background: #16a34a; }
.pill-against { background: #e11d48; }
.agent-name   { font-weight: 700; font-size: 1.05rem; }

.verdict-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #d97706;
}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


def ensure_api_key() -> bool:
    """Use GROQ_API_KEY from the environment/.env, or from Streamlit secrets."""
    if os.environ.get("GROQ_API_KEY"):
        return True
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:  # no secrets file configured
        key = None
    if key:
        os.environ["GROQ_API_KEY"] = key
        return True
    return False


def render_topic(topic: str) -> None:
    st.markdown(
        f'<div class="topic-box"><div class="topic-label">DEBATE TOPIC</div>'
        f'<div class="topic-text">{html.escape(topic)}</div></div>',
        unsafe_allow_html=True,
    )


def render_argument(item: dict) -> None:
    is_for = item["position"] == "FOR"
    side = "for" if is_for else "against"
    icon = "🟢" if is_for else "🔴"

    # FOR always speaks first in a round, so it opens each round section.
    if is_for:
        st.markdown(
            f'<div class="round-badge">ROUND {item["round"]}</div>',
            unsafe_allow_html=True,
        )

    with st.container(key=f"card_{side}_{item['round']}"):
        st.markdown(
            f'<div class="card-head">'
            f'<span class="pill pill-{side}">{icon} {item["position"]}</span>'
            f'<span class="agent-name">{html.escape(item["agent"])}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(item["argument"])


def render_verdict(evaluation: str) -> None:
    st.write("")
    with st.container(key="card_verdict"):
        st.markdown('<div class="verdict-title">⚖️ Judge\'s Verdict</div>', unsafe_allow_html=True)
        st.markdown(evaluation)


def render_result(result: dict) -> None:
    render_topic(result["topic"])
    for item in result["debate_history"]:
        render_argument(item)
    render_verdict(result["evaluation"])


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------

st.markdown(
    '<div class="hero">'
    '<div class="hero-title">🗣️ Multi-Agent Debate</div>'
    '<div class="hero-sub">Two AI agents debate your topic over several rounds, '
    'then an AI judge scores both sides.</div></div>',
    unsafe_allow_html=True,
)

if not ensure_api_key():
    st.error(
        "GROQ_API_KEY is not configured. Add it under **Settings → Secrets** "
        "on Streamlit Cloud (`GROQ_API_KEY = \"...\"`), or put it in a local `.env` file."
    )
    st.stop()

with st.form("debate_form"):
    topic = st.text_input(
        "Debate topic",
        max_chars=300,
        placeholder="e.g. AI should be allowed to make hiring decisions",
    )
    rounds = st.slider("Number of rounds", min_value=1, max_value=4, value=2)
    submitted = st.form_submit_button("Start debate", type="primary", use_container_width=True)

if submitted:
    st.session_state.pop("result", None)
    topic = topic.strip()

    if len(topic) < MIN_TOPIC_CHARS:
        st.warning("Please enter a debate topic.")
    else:
        debate_box = st.container()
        with debate_box:
            render_topic(topic)
        with st.status("Starting debate...", expanded=True) as status:

            def on_progress(event: str, data: dict) -> None:
                if event == "agent_start":
                    status.update(
                        label=f"Round {data['round']}: {data['agent']} ({data['position']}) is preparing an argument..."
                    )
                elif event == "argument":
                    with debate_box:
                        render_argument(data)
                elif event == "judge_start":
                    status.update(label="The judge is evaluating the debate...")

            try:
                result = run_debate(topic, rounds, on_progress=on_progress)
            except DebateError as e:
                status.update(label="Debate failed", state="error")
                st.error(str(e))
            else:
                status.update(label="Debate complete", state="complete", expanded=False)
                st.session_state["result"] = result
                with debate_box:
                    render_verdict(result["evaluation"])

elif "result" in st.session_state:
    render_result(st.session_state["result"])

