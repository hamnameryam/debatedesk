import os
import argparse
from dotenv import load_dotenv
from langchain_groq import ChatGroq
 
 
# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
 
load_dotenv()
 
MODEL_NAME = "openai/gpt-oss-120b"
REQUEST_TIMEOUT = 90  # seconds
MAX_RETRIES = 2
 
 
class DebateError(Exception):
    """Raised when an agent or the judge cannot complete its step."""
 
 
def _make_llm(temperature):
    return ChatGroq(
        model=MODEL_NAME,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        temperature=temperature,
        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )
 
 
# ============================================================
# DEBATE AGENT
# ============================================================
 
class DebateAgent:
 
    def __init__(self, name, position, expertise):
 
        self.name = name
        self.position = position
        self.expertise = expertise
 
        # Store all arguments
        self.arguments = []
 
        # Groq LLM
        self.llm = _make_llm(temperature=0.7)
 
    def make_argument(
        self,
        topic,
        round_number,
        opponent_argument=None
    ):
        """
        Generate an argument for the assigned position.
        """
 
        system_prompt = f"""
You are {self.name}, an expert debate agent.
 
Your area of expertise:
{self.expertise}
 
Your assigned position:
{self.position}
 
You are participating in a structured multi-round debate.
 
Your responsibilities:
 
1. Present a clear and logical argument.
2. Stay focused on the debate topic.
3. Use relevant reasoning and evidence where appropriate.
4. Directly address the opposing argument.
5. Identify weaknesses in the opposing position.
6. Strengthen your own position.
7. Avoid unnecessary repetition.
8. Be professional and respectful.
9. Maintain your assigned position.
 
IMPORTANT:
Keep your response between 400 and 600 words.
Do not use unnecessary tables or excessive sections.
Focus on the strongest arguments.
"""
 
        user_prompt = f"""
Debate Topic:
{topic}
 
Current Round:
{round_number}
 
Your Position:
{self.position}
"""
 
        # Give the previous opponent argument to the agent
        if opponent_argument:
 
            # Prevent huge prompts between agents
            max_opponent_chars = 5000
 
            if len(opponent_argument) > max_opponent_chars:
                opponent_argument = (
                    opponent_argument[:max_opponent_chars]
                    + "\n[Previous argument truncated]"
                )
 
            user_prompt += f"""
 
The opposing agent's previous argument was:
 
{opponent_argument}
 
Respond directly to this argument.
 
Identify its strongest weaknesses,
provide counterarguments,
and strengthen your own position.
"""
 
        user_prompt += """
 
Now provide your debate argument.
Keep it focused, logical, and between 400 and 600 words.
"""
 
        try:
            response = self.llm.invoke(
                [
                    ("system", system_prompt),
                    ("human", user_prompt)
                ]
            )
            argument = response.content
 
        except Exception as e:
            # Stop the debate instead of feeding an error message
            # to the opponent and the judge as if it were an argument.
            raise DebateError(
                f"The {self.position} agent ({self.name}) failed in "
                f"round {round_number}: {e}"
            ) from e
 
        if not argument or not argument.strip():
            raise DebateError(
                f"The {self.position} agent ({self.name}) returned an "
                f"empty response in round {round_number}."
            )
 
        # Save argument
        self.arguments.append(
            {
                "round": round_number,
                "agent": self.name,
                "position": self.position,
                "argument": argument
            }
        )
 
        return argument
 
 
# ============================================================
# AI DEBATE JUDGE
# ============================================================
 
class DebateJudge:
 
    def __init__(self):
 
        # Groq LLM
        self.llm = _make_llm(temperature=0.3)
 
    def evaluate(self, topic, debate_history):
        """
        Evaluate the complete debate.
 
        A shortened version of the arguments is sent
        to the judge to prevent request-size errors.
        """
 
        formatted_debate = ""
 
        for item in debate_history:
 
            argument = item["argument"]
 
            # Limit the amount of text sent to the judge.
            max_chars = 4000
 
            if len(argument) > max_chars:
                argument = (
                    argument[:max_chars]
                    + "\n[Argument truncated for evaluation]"
                )
 
            formatted_debate += f"""
Round {item['round']}
 
Agent:
{item['agent']}
 
Position:
{item['position']}
 
Argument:
{argument}
 
----------------------------------------
"""
 
        system_prompt = """
You are an impartial AI debate judge.
 
Your task is to evaluate a complete multi-round debate objectively.
 
Evaluate BOTH sides based on:
 
1. Quality of reasoning
2. Relevance to the topic
3. Strength of arguments
4. Response to opposing arguments
5. Evidence and supporting logic
6. Clarity
7. Logical consistency
8. Overall persuasiveness
 
Do not judge based on the agent's name.
 
Judge only the arguments.
 
Begin your response with exactly one line in this format, with nothing before it:
SCORES: FOR=<number from 0 to 100>; AGAINST=<number from 0 to 100>
 
Then continue with your final evaluation, which must contain:
 
1. Winner
2. FOR score out of 100
3. AGAINST score out of 100
4. Strongest FOR argument
5. Strongest AGAINST argument
6. Key insights
7. Final synthesis
 
Keep the evaluation concise and clear.
"""
 
        user_prompt = f"""
Debate Topic:
 
{topic}
 
Complete Debate:
 
{formatted_debate}
 
Evaluate the complete debate objectively.
 
Provide the final result in a clear format.
"""
 
        try:
            response = self.llm.invoke(
                [
                    ("system", system_prompt),
                    ("human", user_prompt)
                ]
            )
            evaluation = response.content
 
        except Exception as e:
            raise DebateError(f"The AI Judge failed: {e}") from e
 
        if not evaluation or not evaluation.strip():
            raise DebateError("The AI Judge returned an empty response.")
 
        return evaluation
 
 
# ============================================================
# RUN DEBATE
# ============================================================
 
def run_debate(topic, rounds=2, on_progress=None):
    """
    Run the full debate.
 
    on_progress(event, data) is called as the debate advances so a UI
    can show live updates. Events:
        "agent_start"  -> {"round", "agent", "position"}
        "argument"     -> {"round", "agent", "position", "argument"}
        "judge_start"  -> {}
    """
 
    def notify(event, data=None):
        if on_progress:
            on_progress(event, data or {})
 
    pro_agent = DebateAgent(
        name="Dr. Alex Chen",
        position="FOR",
        expertise=(
            "Technology, artificial intelligence, "
            "research, innovation, and future technologies."
        )
    )
 
    con_agent = DebateAgent(
        name="Prof. Sarah Martinez",
        position="AGAINST",
        expertise=(
            "Ethics, social sciences, critical thinking, "
            "risk analysis, and social impact."
        )
    )
 
    judge = DebateJudge()
 
    # Complete debate history
    debate_history = []
 
    # Previous argument
    previous_argument = None
 
    for round_number in range(1, rounds + 1):
 
        # ---------------- FOR ----------------
        notify("agent_start", {
            "round": round_number,
            "agent": pro_agent.name,
            "position": pro_agent.position,
        })
 
        pro_argument = pro_agent.make_argument(
            topic=topic,
            round_number=round_number,
            opponent_argument=previous_argument
        )
 
        item = {
            "round": round_number,
            "agent": pro_agent.name,
            "position": pro_agent.position,
            "argument": pro_argument
        }
        debate_history.append(item)
        notify("argument", item)
 
        # -------------- AGAINST --------------
        notify("agent_start", {
            "round": round_number,
            "agent": con_agent.name,
            "position": con_agent.position,
        })
 
        con_argument = con_agent.make_argument(
            topic=topic,
            round_number=round_number,
            opponent_argument=pro_argument
        )
 
        item = {
            "round": round_number,
            "agent": con_agent.name,
            "position": con_agent.position,
            "argument": con_argument
        }
        debate_history.append(item)
        notify("argument", item)
 
        # AGAINST becomes previous argument
        # for FOR in the next round.
        previous_argument = con_argument
 
    # ---------------- JUDGE ----------------
    notify("judge_start")
 
    evaluation = judge.evaluate(
        topic=topic,
        debate_history=debate_history
    )
 
    return {
        "topic": topic,
        "rounds": rounds,
        "debate_history": debate_history,
        "evaluation": evaluation
    }
 
 
# ============================================================
# COMMAND LINE (optional, for local testing)
# ============================================================
 
def _print_progress(event, data):
    if event == "agent_start":
        print(f"\n[Round {data['round']}] {data['agent']} ({data['position']}) is preparing an argument...")
    elif event == "argument":
        print(f"\n--- {data['position']} ARGUMENT ---\n{data['argument']}")
    elif event == "judge_start":
        print("\nThe AI Judge is evaluating the debate...")
 
 
def main():
 
    parser = argparse.ArgumentParser(
        description="Multi-Agent Debate System using LangChain and Groq"
    )
    parser.add_argument("--topic", type=str, required=True, help="Topic for the debate")
    parser.add_argument("--rounds", type=int, default=2, help="Number of debate rounds (default: 2)")
    args = parser.parse_args()
 
    rounds = max(1, min(args.rounds, 4))
 
    if not os.environ.get("GROQ_API_KEY"):
        print("\nERROR: GROQ_API_KEY is not set.")
        return
 
    try:
        result = run_debate(args.topic, rounds, on_progress=_print_progress)
    except DebateError as e:
        print(f"\nERROR: {e}")
        return
 
    print("\n--- FINAL EVALUATION ---")
    print(result["evaluation"])
 
 
if __name__ == "__main__":
    main()

