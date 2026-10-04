import os

import streamlit as st

from agent import DebateError, run_debate

st.set_page_config(page_title="Multi-Agent Debate", page_icon="🗣️", layout="centered")

AVATARS = {"FOR": "🟢", "AGAINST": "🔴"}
MIN_TOPIC_CHARS = 3


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


def render_argument(item: dict) -> None:
    # FOR always speaks first in a round, so it opens each round section.
    if item["position"] == "FOR":
        st.subheader(f"Round {item['round']}")
    with st.chat_message(item["position"], avatar=AVATARS[item["position"]]):
        st.markdown(f"**{item['agent']}** · {item['position']}")
        st.markdown(item["argument"])


def render_verdict(evaluation: str) -> None:
    st.divider()
    st.subheader("⚖️ Judge's verdict")
    with st.container(border=True):
        st.markdown(evaluation)


def render_result(result: dict) -> None:
    st.markdown(f"### Topic: {result['topic']}")
    for item in result["debate_history"]:
        render_argument(item)
    render_verdict(result["evaluation"])


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------

st.title("🗣️ Multi-Agent Debate")
st.caption(
    "Two AI agents debate your topic over several rounds, "
    "then an AI judge scores both sides."
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
