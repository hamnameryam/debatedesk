import html
import os
import re
 
import streamlit as st
 
from agent import DebateError, run_debate
 
st.set_page_config(page_title="DebateDesk", page_icon="🎙️", layout="wide")
 
MIN_TOPIC_CHARS = 3
 
PANEL = {
    "FOR": {
        "name": "Dr. Alex Chen",
        "role": "Technology & innovation",
        "desc": "Argues in favour, drawing on technology, AI and research.",
    },
    "AGAINST": {
        "name": "Prof. Sarah Martinez",
        "role": "Ethics & social impact",
        "desc": "Argues against, drawing on ethics, risk analysis and society.",
    },
    "JUDGE": {
        "name": "AI Judge",
        "role": "Impartial evaluator",
        "desc": "Scores both sides on reasoning, evidence and clarity.",
    },
}
 
EXAMPLES = [
    "AI should replace human teachers in schools",
    "Remote work is better than office work",
    "Social media does more harm than good",
]
 
STYLE = """
<style>
footer { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 4.5rem; padding-bottom: 3rem; }
 
/* ---------- Hero ---------- */
.hero {
    display: flex; align-items: center; gap: 1.4rem;
    background: linear-gradient(135deg, #0b1220 0%, #1e1b4b 55%, #312e81 100%);
    border-radius: 20px; padding: 1.7rem 1.9rem; margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, .35);
}
.logo { position: relative; width: 58px; height: 58px; flex: none; }
.logo .b1 { position: absolute; left: 0; top: 0; width: 38px; height: 30px;
            border-radius: 11px 11px 11px 3px; background: #10b981; }
.logo .b2 { position: absolute; right: 0; bottom: 0; width: 38px; height: 30px;
            border-radius: 11px 11px 3px 11px; background: #f43f5e;
            box-shadow: -3px -3px 0 #1e1b4b; }
.hero-title { color: #fff; font-size: 2.3rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; }
.hero-title span { color: #a5b4fc; }
.hero-sub { color: rgba(255,255,255,.82); margin-top: .35rem; font-size: 1rem; }
.chips { display: flex; gap: .5rem; margin-top: .8rem; flex-wrap: wrap; }
.chip { font-size: .72rem; font-weight: 700; letter-spacing: .08em; color: #e0e7ff;
        background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.18);
        padding: .2rem .7rem; border-radius: 999px; }
 
/* ---------- Section headers ---------- */
.section { display: flex; align-items: center; gap: .7rem; margin: 2rem 0 1rem; }
.section-num { font-weight: 800; font-size: .8rem; color: #fff; background: #6366f1;
               border-radius: 8px; padding: .2rem .55rem; letter-spacing: .05em; }
.section-title { font-size: 1.25rem; font-weight: 800; }
.section-line { flex: 1; height: 1px; background: rgba(128,128,128,.3); }
 
/* ---------- Form ---------- */
[data-testid="stForm"] {
    border: 1px solid rgba(99, 102, 241, .35); border-radius: 16px; padding: 1.4rem;
    background: rgba(99, 102, 241, .05);
}
[data-testid="stForm"] [data-testid="stHorizontalBlock"] { align-items: flex-end; }
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #4f46e5, #6366f1); color: #fff; border: 0;
    font-weight: 700; border-radius: 10px; height: 2.8rem;
}
[data-testid="stFormSubmitButton"] button:hover { filter: brightness(1.12); color: #fff; }
[class*="st-key-ex_"] button { border-radius: 999px; font-size: .85rem;
                               border: 1px dashed rgba(99,102,241,.6); }
 
/* ---------- Panel (empty state) ---------- */
.panel { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.panel-card { border-radius: 14px; padding: 1.2rem; border: 1px solid; }
.panel-card.for     { border-color: rgba(16,185,129,.4); background: rgba(16,185,129,.07); }
.panel-card.against { border-color: rgba(244,63,94,.4);  background: rgba(244,63,94,.06); }
.panel-card.judge   { border-color: rgba(245,158,11,.45); background: rgba(245,158,11,.08); }
.p-name { font-weight: 800; font-size: 1.05rem; margin-top: .7rem; }
.p-role { font-size: .85rem; opacity: .65; }
.p-desc { font-size: .92rem; margin-top: .5rem; opacity: .85; }
 
/* ---------- Topic ---------- */
.topic-box { border-radius: 14px; padding: .9rem 1.2rem; margin-bottom: .4rem;
             background: rgba(99,102,241,.10); border: 1px solid rgba(99,102,241,.35); }
.topic-label { font-size: .72rem; font-weight: 800; letter-spacing: .12em; color: #6366f1; }
.topic-text { font-size: 1.2rem; font-weight: 700; margin-top: .15rem; }
 
/* ---------- Rounds ---------- */
.round-bar { display: flex; align-items: center; gap: .6rem; margin: 1.5rem 0 .7rem; }
.round-num { width: 30px; height: 30px; border-radius: 50%; background: #4f46e5; color: #fff;
             display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: .85rem; }
.round-title { font-weight: 800; letter-spacing: .08em; font-size: .85rem; text-transform: uppercase; }
.round-of { opacity: .5; font-size: .8rem; }
.round-line { flex: 1; height: 1px; background: rgba(128,128,128,.3); }
 
/* ---------- Cards ---------- */
[class*="st-key-card_for_"], [class*="st-key-card_against_"], [class*="st-key-card_verdict"] {
    border-radius: 14px; padding: 1.1rem 1.3rem 1.2rem; box-shadow: 0 2px 10px rgba(0,0,0,.06);
}
[class*="st-key-card_for_"]     { background: rgba(16,185,129,.08); border: 1px solid rgba(16,185,129,.35); border-top: 5px solid #10b981; }
[class*="st-key-card_against_"] { background: rgba(244,63,94,.07);  border: 1px solid rgba(244,63,94,.35);  border-top: 5px solid #f43f5e; }
[class*="st-key-card_verdict"]  { background: rgba(245,158,11,.09); border: 1px solid rgba(245,158,11,.45); border-top: 5px solid #f59e0b; }
 
[class*="st-key-card_"] h1, [class*="st-key-card_"] h2,
[class*="st-key-card_"] h3, [class*="st-key-card_"] h4 {
    font-size: 1.05rem !important; padding: 0; margin: .8rem 0 .3rem;
}
[class*="st-key-card_"] hr { margin: .9rem 0; }
 
.card-head { display: flex; align-items: center; gap: .75rem; margin-bottom: .4rem; }
.avatar { width: 40px; height: 40px; border-radius: 50%; color: #fff; flex: none;
          display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: .95rem; }
.avatar-for { background: #10b981; } .avatar-against { background: #f43f5e; } .avatar-judge { background: #f59e0b; }
.who { flex: 1; }
.agent-name { font-weight: 800; font-size: 1.02rem; line-height: 1.2; }
.agent-role { font-size: .8rem; opacity: .65; }
.pill { padding: .2rem .75rem; border-radius: 999px; color: #fff; font-weight: 800;
        font-size: .75rem; letter-spacing: .08em; }
.pill-for { background: #059669; } .pill-against { background: #e11d48; }
 
/* ---------- Pending placeholders ---------- */
.pending { border: 2px dashed; border-radius: 14px; padding: 1.4rem; text-align: center; font-weight: 600; }
.pending-for     { border-color: rgba(16,185,129,.55); color: #059669; background: rgba(16,185,129,.04); }
.pending-against { border-color: rgba(244,63,94,.55);  color: #e11d48; background: rgba(244,63,94,.04); }
.pending-judge   { border-color: rgba(245,158,11,.6);  color: #d97706; background: rgba(245,158,11,.05); }
.pending.idle { opacity: .6; }
.dots i { display: inline-block; width: 6px; height: 6px; margin-left: 4px; border-radius: 50%;
          background: currentColor; animation: blink 1.2s infinite both; }
.dots i:nth-child(2) { animation-delay: .2s; } .dots i:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 80%, 100% { opacity: .2; } 40% { opacity: 1; } }
 
/* ---------- Scoreboard ---------- */
.scoreboard { display: grid; grid-template-columns: 1fr auto 1fr; gap: 1rem; align-items: center; margin-bottom: .8rem; }
.score { border-radius: 14px; padding: 1rem 1.2rem; border: 1px solid; }
.score.for     { border-color: rgba(16,185,129,.4); background: rgba(16,185,129,.08); }
.score.against { border-color: rgba(244,63,94,.4);  background: rgba(244,63,94,.07); }
.score.win.for     { box-shadow: 0 0 0 3px rgba(16,185,129,.4); }
.score.win.against { box-shadow: 0 0 0 3px rgba(244,63,94,.4); }
.s-label { font-size: .75rem; font-weight: 800; letter-spacing: .1em; }
.s-num { font-size: 2.4rem; font-weight: 800; line-height: 1.1; }
.s-num small { font-size: .9rem; opacity: .6; margin-left: .2rem; }
.bar { height: 8px; background: rgba(128,128,128,.22); border-radius: 999px; overflow: hidden; margin-top: .5rem; }
.bar span { display: block; height: 100%; border-radius: 999px; }
.score.for .bar span { background: #10b981; } .score.against .bar span { background: #f43f5e; }
.score-vs { font-weight: 800; opacity: .5; }
.winner { text-align: center; font-weight: 800; font-size: 1.1rem; padding: .7rem; border-radius: 12px;
          margin-bottom: 1rem; border: 1px solid rgba(245,158,11,.45);
          background: linear-gradient(90deg, rgba(245,158,11,.18), rgba(245,158,11,.06)); }
.verdict-title { font-size: 1.2rem; font-weight: 800; color: #d97706; margin-bottom: .3rem; }
 
.footer { text-align: center; opacity: .55; font-size: .8rem; margin-top: 2.5rem; }
 
@media (max-width: 760px) {
    .panel, .scoreboard { grid-template-columns: 1fr; }
    .hero-title { font-size: 1.8rem; }
}
</style>
"""
 
st.markdown(STYLE, unsafe_allow_html=True)
 
 
# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
 
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
 
 
def initials(name: str) -> str:
    words = [w for w in name.split() if not w.endswith(".")]
    return "".join(w[0] for w in words[:2]).upper() or "?"
 
 
def safe_md(text: str) -> str:
    # Stop "$5M ... $10M" from being rendered as LaTeX math.
    return text.replace("$", "\\$")
 
 
def parse_scores(text: str):
    """Return (for_score, against_score, text_without_score_line); scores may be None."""
    line_re = re.compile(
        r"SCORES?\s*:?\**\s*FOR\s*=\s*(\d{1,3})\D{1,12}AGAINST\s*=\s*(\d{1,3})", re.I
    )
    m = line_re.search(text)
    if m:
        cleaned = "\n".join(l for l in text.splitlines() if not line_re.search(l)).strip()
        sf, sa = int(m.group(1)), int(m.group(2))
    else:
        def find(label):
            mm = re.search(
                rf"\b{label}\b[^\n\d]{{0,40}}?(\d{{1,3}})\s*(?:/|out of)\s*100", text, re.I
            )
            return int(mm.group(1)) if mm else None
 
        sf, sa, cleaned = find("FOR"), find("AGAINST"), text
    if sf is None or sa is None:
        return None, None, cleaned
    return min(sf, 100), min(sa, 100), cleaned
 
 
def pending_html(side: str, text: str, active: bool = True) -> str:
    dots = '<span class="dots"><i></i><i></i><i></i></span>' if active else ""
    idle = "" if active else " idle"
    return f'<div class="pending pending-{side}{idle}">{html.escape(text)} {dots}</div>'
 
 
# ----------------------------------------------------------------------------
# Renderers
# ----------------------------------------------------------------------------
 
def section(num: str, title: str) -> None:
    st.markdown(
        f'<div class="section"><span class="section-num">{num}</span>'
        f'<span class="section-title">{title}</span><span class="section-line"></span></div>',
        unsafe_allow_html=True,
    )
 
 
def render_hero() -> None:
    st.markdown(
        '<div class="hero"><div class="logo"><div class="b1"></div><div class="b2"></div></div>'
        '<div><div class="hero-title">Debate<span>Desk</span></div>'
        '<div class="hero-sub">Two AI debaters. One impartial judge. '
        'Pick a topic and watch the arguments unfold.</div>'
        '<div class="chips"><span class="chip">🟢 FOR</span><span class="chip">🔴 AGAINST</span>'
        '<span class="chip">⚖️ JUDGE</span></div></div></div>',
        unsafe_allow_html=True,
    )
 
 
def render_panel() -> None:
    cards = ""
    for key, side in (("FOR", "for"), ("AGAINST", "against"), ("JUDGE", "judge")):
        p = PANEL[key]
        cards += (
            f'<div class="panel-card {side}"><div class="avatar avatar-{side}">{initials(p["name"])}</div>'
            f'<div class="p-name">{html.escape(p["name"])}</div>'
            f'<div class="p-role">{key} · {html.escape(p["role"])}</div>'
            f'<div class="p-desc">{html.escape(p["desc"])}</div></div>'
        )
    st.markdown(f'<div class="panel">{cards}</div>', unsafe_allow_html=True)
 
 
def render_topic(topic: str) -> None:
    st.markdown(
        f'<div class="topic-box"><div class="topic-label">DEBATE TOPIC</div>'
        f'<div class="topic-text">{html.escape(topic)}</div></div>',
        unsafe_allow_html=True,
    )
 
 
def round_columns(number: int, total: int):
    st.markdown(
        f'<div class="round-bar"><span class="round-num">{number}</span>'
        f'<span class="round-title">Round {number}</span><span class="round-of">of {total}</span>'
        f'<span class="round-line"></span></div>',
        unsafe_allow_html=True,
    )
    return st.columns(2, gap="medium")
 
 
def render_card(item: dict) -> None:
    side = "for" if item["position"] == "FOR" else "against"
    role = PANEL[item["position"]]["role"]
    with st.container(key=f"card_{side}_{item['round']}"):
        st.markdown(
            f'<div class="card-head"><div class="avatar avatar-{side}">{initials(item["agent"])}</div>'
            f'<div class="who"><div class="agent-name">{html.escape(item["agent"])}</div>'
            f'<div class="agent-role">{html.escape(role)}</div></div>'
            f'<span class="pill pill-{side}">{item["position"]}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(safe_md(item["argument"]))
 
 
def render_verdict(evaluation: str) -> None:
    score_for, score_against, body = parse_scores(evaluation)
 
    if score_for is not None:
        if score_for > score_against:
            winner = f"🏆 Winner: FOR · {PANEL['FOR']['name']}"
        elif score_against > score_for:
            winner = f"🏆 Winner: AGAINST · {PANEL['AGAINST']['name']}"
        else:
            winner = "🤝 It's a tie"
        win_for = " win" if score_for > score_against else ""
        win_against = " win" if score_against > score_for else ""
        st.markdown(
            f'<div class="scoreboard">'
            f'<div class="score for{win_for}"><div class="s-label">FOR · {html.escape(PANEL["FOR"]["name"])}</div>'
            f'<div class="s-num">{score_for}<small>/100</small></div>'
            f'<div class="bar"><span style="width:{score_for}%"></span></div></div>'
            f'<div class="score-vs">VS</div>'
            f'<div class="score against{win_against}"><div class="s-label">AGAINST · {html.escape(PANEL["AGAINST"]["name"])}</div>'
            f'<div class="s-num">{score_against}<small>/100</small></div>'
            f'<div class="bar"><span style="width:{score_against}%"></span></div></div></div>'
            f'<div class="winner">{html.escape(winner)}</div>',
            unsafe_allow_html=True,
        )
 
    with st.container(key="card_verdict"):
        st.markdown('<div class="verdict-title">⚖️ Judge\'s evaluation</div>', unsafe_allow_html=True)
        st.markdown(safe_md(body))
 
 
def render_result(result: dict) -> None:
    section("02", "Debate")
    render_topic(result["topic"])
 
    by_round: dict = {}
    for item in result["debate_history"]:
        by_round.setdefault(item["round"], {})[item["position"]] = item
 
    for number in sorted(by_round):
        col_for, col_against = round_columns(number, result["rounds"])
        with col_for:
            render_card(by_round[number]["FOR"])
        with col_against:
            render_card(by_round[number]["AGAINST"])
 
    section("03", "Verdict")
    render_verdict(result["evaluation"])
 
 
# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
 
render_hero()
 
if not ensure_api_key():
    st.error(
        "GROQ_API_KEY is not configured. Add it under **Settings → Secrets** "
        "on Streamlit Cloud (`GROQ_API_KEY = \"...\"`), or put it in a local `.env` file."
    )
    st.stop()
 
 
def use_example(text: str) -> None:
    st.session_state["topic_input"] = text
 
 
section("01", "Setup")
 
st.caption("Try an example:")
example_cols = st.columns(len(EXAMPLES))
for i, (col, example) in enumerate(zip(example_cols, EXAMPLES)):
    col.button(example, key=f"ex_{i}", on_click=use_example, args=(example,), use_container_width=True)
 
with st.form("debate_form"):
    topic = st.text_input(
        "Debate topic",
        key="topic_input",
        max_chars=300,
        placeholder="e.g. AI should be allowed to make hiring decisions",
    )
    slider_col, button_col = st.columns([3, 1], gap="large")
    rounds = slider_col.slider("Number of rounds", min_value=1, max_value=4, value=2)
    submitted = button_col.form_submit_button("Start debate", type="primary", use_container_width=True)
 
if submitted:
    st.session_state.pop("result", None)
    topic = topic.strip()
 
    if len(topic) < MIN_TOPIC_CHARS:
        st.warning("Please enter a debate topic.")
    else:
        section("02", "Debate")
        status = st.status("Starting debate...", expanded=False)
        render_topic(topic)
        debate_box = st.container()
        verdict_box = st.container()
 
        slots: dict = {}
        pending: set = set()
 
        def show_pending(key, side, text, active=True):
            slots[key].markdown(pending_html(side, text, active), unsafe_allow_html=True)
            pending.add(key)
 
        def on_progress(event: str, data: dict) -> None:
            if event == "agent_start":
                number, side = data["round"], data["position"]
                status.update(
                    label=f"Round {number} of {rounds}: {data['agent']} ({side}) is drafting an argument..."
                )
                if side == "FOR":
                    with debate_box:
                        col_for, col_against = round_columns(number, rounds)
                    slots[(number, "FOR")] = col_for.empty()
                    slots[(number, "AGAINST")] = col_against.empty()
                    show_pending((number, "AGAINST"), "against", "Waiting for their turn", active=False)
                show_pending((number, side), side.lower(), f"{data['agent']} is drafting")
 
            elif event == "argument":
                key = (data["round"], data["position"])
                with slots[key].container():
                    render_card(data)
                pending.discard(key)
 
            elif event == "judge_start":
                status.update(label="The judge is deliberating...")
                with verdict_box:
                    section("03", "Verdict")
                    slots["verdict"] = st.empty()
                show_pending("verdict", "judge", "The judge is deliberating")
 
        try:
            result = run_debate(topic, rounds, on_progress=on_progress)
        except DebateError as e:
            for key in list(pending):
                slots[key].empty()
            status.update(label="Debate failed", state="error")
            st.error(str(e))
        else:
            status.update(label="Debate complete", state="complete")
            st.session_state["result"] = result
            with slots["verdict"].container():
                render_verdict(result["evaluation"])
 
elif "result" in st.session_state:
    render_result(st.session_state["result"])
 
else:
    section("02", "Meet the panel")
    render_panel()
 
st.markdown(
    '<div class="footer">DebateDesk · Powered by Groq · Arguments are AI-generated; '
    'cited studies and statistics may not be real.</div>',
    unsafe_allow_html=True,
)
 
