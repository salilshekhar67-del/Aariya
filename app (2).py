import matplotlib
matplotlib.use('Agg')  # Must be before any other matplotlib imports — prevents display errors on servers
import streamlit as st
import json
import re
import io
import os
from typing import List, Optional, Annotated
from typing import TypedDict

# ── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="HR Coaching Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Dark professional theme */
.stApp {
    background: #0f1117;
    color: #e8e8e8;
}

.main-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0f1117 50%, #1a1f2e 100%);
    border: 1px solid #2a3045;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 50%, rgba(99, 179, 237, 0.06) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 50%, rgba(154, 117, 234, 0.06) 0%, transparent 60%);
    pointer-events: none;
}

.main-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: #e8e8e8;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}

.main-header p {
    color: #8892a4;
    font-size: 1rem;
    margin: 0;
    font-weight: 300;
}

.accent-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, #63b3ed, #9a75ea);
    margin-right: 10px;
    vertical-align: middle;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d1018 !important;
    border-right: 1px solid #1e2535 !important;
}

[data-testid="stSidebar"] .sidebar-section {
    background: #141824;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}

.sidebar-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: #4a5568;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

/* Chat messages */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 0;
}

.msg-user {
    background: linear-gradient(135deg, #1e3a5f, #1a3050);
    border: 1px solid #2a4a7f;
    border-radius: 16px 16px 4px 16px;
    padding: 1rem 1.4rem;
    margin-left: 15%;
    color: #dce8f5;
    font-size: 0.95rem;
    line-height: 1.6;
}

.msg-assistant {
    background: #141824;
    border: 1px solid #1e2535;
    border-radius: 16px 16px 16px 4px;
    padding: 1rem 1.4rem;
    margin-right: 10%;
    color: #d4d8e2;
    font-size: 0.95rem;
    line-height: 1.6;
}

.msg-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.msg-user .msg-label { color: #63b3ed; }
.msg-assistant .msg-label { color: #9a75ea; }

/* Metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.metric-card {
    background: #141824;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}

.metric-card:hover { border-color: #2a3a55; }

.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #63b3ed;
    line-height: 1;
    margin-bottom: 0.3rem;
}

.metric-label {
    font-size: 0.72rem;
    color: #6b7280;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    margin: 0.15rem;
}

.badge-blue   { background: rgba(99,179,237,0.12); color: #63b3ed; border: 1px solid rgba(99,179,237,0.2); }
.badge-purple { background: rgba(154,117,234,0.12); color: #9a75ea; border: 1px solid rgba(154,117,234,0.2); }
.badge-green  { background: rgba(72,187,120,0.12); color: #48bb78; border: 1px solid rgba(72,187,120,0.2); }
.badge-amber  { background: rgba(246,173,85,0.12); color: #f6ad55; border: 1px solid rgba(246,173,85,0.2); }

/* Input area */
.stTextArea textarea {
    background: #141824 !important;
    border: 1px solid #1e2535 !important;
    color: #e8e8e8 !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextArea textarea:focus {
    border-color: #63b3ed !important;
    box-shadow: 0 0 0 2px rgba(99,179,237,0.1) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e3a5f, #2a4a7f) !important;
    color: #dce8f5 !important;
    border: 1px solid #2a4a7f !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s !important;
    font-size: 0.9rem !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2a4a7f, #3a5a8f) !important;
    border-color: #63b3ed !important;
    transform: translateY(-1px) !important;
}

/* Section header */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #c8d0dc;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2535;
}

/* Alert box */
.info-box {
    background: rgba(99,179,237,0.06);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    color: #8bb8d8;
    font-size: 0.88rem;
    line-height: 1.5;
}

.warn-box {
    background: rgba(246,173,85,0.06);
    border: 1px solid rgba(246,173,85,0.2);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    color: #c8965a;
    font-size: 0.88rem;
}

/* selectbox, text_input */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #141824 !important;
    border-color: #1e2535 !important;
    color: #e8e8e8 !important;
    border-radius: 10px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1018; }
::-webkit-scrollbar-thumb { background: #2a3045; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3a4055; }

/* Divider */
hr { border-color: #1e2535 !important; }

/* Tag pill row */
.pill-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── LLM Factory ────────────────────────────────────────
def get_llm(provider: str, api_key: str, model: str):
    if provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key, temperature=0.3)
    elif provider == "Anthropic (Claude)":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, temperature=0.3)
    elif provider == "Groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key, temperature=0.3)
    elif provider == "OpenRouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


PROVIDER_MODELS = {
    "OpenAI": [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"
    ],
    "Anthropic (Claude)": [
        "claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5-20251001"
    ],
    "Groq": [
        "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
        "mixtral-8x7b-32768", "gemma2-9b-it"
    ],
    "OpenRouter": [
        "openai/gpt-4o", "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3.3-70b-instruct", "google/gemini-flash-1.5",
        "mistralai/mixtral-8x7b-instruct"
    ]
}



# ── Build LangGraph Agent ──────────────────────────────
def build_agent(llm):
    from typing import TypedDict, List, Optional, Annotated
    from langchain_core.messages import BaseMessage, HumanMessage
    from langchain_core.tools import tool
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_experimental.tools import PythonAstREPLTool
    from langgraph.graph import StateGraph, END, START
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import RemoveMessage
    from langgraph.graph.message import add_messages
    import json, io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    # ── State ──────────────────────────────────────────
    class HRState(TypedDict):
        messages:          Annotated[List[BaseMessage], add_messages]
        hr_name:           str
        transcript:        str
        category:          str
        sentiment_score:   float
        empathy_score:     float
        tone_flags:        List[str]
        keywords:          List[str]
        strengths:         List[str]
        improvement_areas: List[str]
        # coaching guide stored as 4 flat fields — no nested objects
        consultation_overview: str
        improvements:          List[str]
        suggest_actions:       List[str]
        future_plan:           List[str]
        duration:          str
        pdf_bytes:         Optional[bytes]

    # ── Tools ───────────────────────────────────────────
    @tool
    def python_repl(code: str) -> str:
        """Execute Python code for data analysis and scoring calculations."""
        try:
            if any(k in code.lower() for k in ['import os', 'import sys', 'exec(', 'eval(', 'shutil', '__import__']):
                return "Prohibited keywords detected!"
            safe_code = (
                "import matplotlib\nmatplotlib.use(\'Agg\')\n"
                "import matplotlib.pyplot as plt\n"
                "import warnings\nwarnings.filterwarnings(\'ignore\')\n"
                + code.replace("plt.show()", "plt.savefig(\'/tmp/chart.png\', bbox_inches=\'tight\'); plt.close(\'all\')")
            )
            repl = PythonAstREPLTool()
            result = repl.run(safe_code)
            return f"Visualization executed successfully. Result: {result}"
        except Exception as e:
            return f"Code executed with note: {str(e)}"

    @tool
    def pdf_tool_node(
        hr_name: str,
        duration: str,
        category: str,
        sentiment_score: float,
        empathy_score: float,
        tone_flags: List[str],
        keywords: List[str],
        strengths: List[str],
        improvement_areas: List[str],
        consultation_overview: str,
        improvements: List[str],
        suggest_actions: List[str],
        future_plan: List[str],
        transcript: str,
    ) -> str:
        """Generate the final PDF report. Call this at the end of every session.
        All parameters are flat — strings or lists of strings only. No nested objects.
        - consultation_overview: plain text summary (string)
        - improvements: list of strings
        - suggest_actions: list of strings
        - future_plan: list of strings (each item is "Title by Author")
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story  = []

        story.append(Paragraph("HR Coaching Guide Report", styles["Title"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"HR Name: {hr_name or 'N/A'}", styles["Normal"]))
        story.append(Paragraph(f"Duration: {duration or 'N/A'}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Overview", styles["Heading2"]))
        story.append(Paragraph(f"<b>Category:</b> {category or 'N/A'}", styles["BodyText"]))
        story.append(Paragraph(f"<b>Sentiment Score:</b> {sentiment_score}", styles["BodyText"]))
        story.append(Paragraph(f"<b>Empathy Score:</b> {empathy_score}", styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Tone Flags", styles["Heading2"]))
        for flag in (tone_flags or []):
            story.append(Paragraph(f"• {flag}", styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Keywords", styles["Heading2"]))
        story.append(Paragraph(", ".join(keywords or []) or "None", styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Strengths", styles["Heading2"]))
        for s in (strengths or []):
            story.append(Paragraph(f"• {s}", styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Improvement Areas", styles["Heading2"]))
        for item in (improvement_areas or []):
            story.append(Paragraph(f"• {item}", styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Coaching Guide", styles["Heading2"]))

        if consultation_overview:
            story.append(Paragraph("Consultation Overview", styles["Heading3"]))
            story.append(Paragraph(str(consultation_overview), styles["BodyText"]))
            story.append(Spacer(1, 8))

        for section_items, section_title in [
            (improvements,    "Improvements"),
            (suggest_actions, "Suggested Actions"),
            (future_plan,     "Future Learning Plan"),
        ]:
            if section_items:
                story.append(Paragraph(section_title, styles["Heading3"]))
                for i, item in enumerate(section_items, 1):
                    if isinstance(item, dict):
                        item = f"{item.get('title', '')} — {item.get('author', '')}".strip(" —")
                    story.append(Paragraph(f"{i}. {str(item)}", styles["BodyText"]))
                    story.append(Spacer(1, 4))

        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Transcript", styles["Heading2"]))
        story.append(Paragraph(str(transcript or "No transcript available."), styles["BodyText"]))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        st.session_state["pdf_bytes"]    = pdf_bytes
        st.session_state["pdf_filename"] = f"HR_Report_{hr_name or 'report'}.pdf"
        return f"✅ PDF report generated successfully for {hr_name}."

    tools = [python_repl, pdf_tool_node]

    # ── Analyze Prompt ──────────────────────────────────
    # NOTE: coaching guide fields are extracted as flat strings — NO nested object
    analyze_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert HR coach analyst.
Analyze the HR call transcript and return ONLY a valid JSON object with these exact fields.
NO markdown fences. NO extra text. NO nested objects.

{{
    "category": "one of: Onboarding / Performance Review / Grievance / Exit Interview / General HR",
    "sentiment_score": 0.0,
    "empathy_score": 0.0,
    "tone_flags": ["label1", "label2", "label3", "label4", "label5"],
    "keywords": ["kw1","kw2","kw3","kw4","kw5","kw6","kw7","kw8","kw9","kw10"],
    "strengths": ["strength1", "strength2", "strength3"],
    "improvement_areas": ["What was missing: X | What should have been said/done: Y", "...", "..."],
    "consultation_overview": "2-3 sentence plain text summary here",
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "suggest_actions": ["action1", "action2", "action3", "action4"],
    "future_plan": ["Book Title by Author Name", "Book Title by Author Name", "Book Title by Author Name"]
}}

RULES:
- tone_flags: exactly 5 strings
- keywords: exactly 10 strings
- strengths: exactly 3 strings
- improvement_areas: exactly 3 strings
- improvements: exactly 3 strings
- suggest_actions: exactly 4 strings
- future_plan: exactly 3 plain strings like "Drive by Daniel H. Pink"
- All values must be strings or arrays of strings — no nested objects anywhere"""),
        ("human", "HR Name: {hr_name}\nTranscript: {transcript}")
    ])

    # ── Analyze Transcript Node ─────────────────────────
    def analyze_transcript(state: HRState) -> dict:
        transcript = state.get("transcript", "")
        hr_name    = state.get("hr_name", "")
        if not transcript.strip():
            return {}
        chain    = analyze_prompt | llm
        response = chain.invoke({"hr_name": hr_name, "transcript": transcript})
        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$",          "", raw)
            data = json.loads(raw)

            summary = f"""Transcript analysis complete for {hr_name}.
Scores  → Sentiment: {data.get("sentiment_score")}, Empathy: {data.get("empathy_score")}
Category: {data.get("category")}

Now do these steps IN ORDER:
1. Call python_repl with code to make a bar chart of sentiment_score={data.get("sentiment_score")} and empathy_score={data.get("empathy_score")}.
2. Call pdf_tool_node with these EXACT flat values (do NOT nest them):
   hr_name="{hr_name}"
   duration="{state.get("duration","N/A")}"
   category="{data.get("category","General HR")}"
   sentiment_score={data.get("sentiment_score",0.5)}
   empathy_score={data.get("empathy_score",0.5)}
   tone_flags={data.get("tone_flags",[])}
   keywords={data.get("keywords",[])}
   strengths={data.get("strengths",[])}
   improvement_areas={data.get("improvement_areas",[])}
   consultation_overview="{data.get("consultation_overview","")}"
   improvements={data.get("improvements",[])}
   suggest_actions={data.get("suggest_actions",[])}
   future_plan={data.get("future_plan",[])}
   transcript="{transcript[:300]}..." """

            return {{
                "category":             data.get("category", "General HR"),
                "sentiment_score":      float(data.get("sentiment_score", 0.5)),
                "empathy_score":        float(data.get("empathy_score", 0.5)),
                "tone_flags":           data.get("tone_flags", []),
                "keywords":             data.get("keywords", []),
                "strengths":            data.get("strengths", []),
                "improvement_areas":    data.get("improvement_areas", []),
                "consultation_overview": data.get("consultation_overview", ""),
                "improvements":         data.get("improvements", []),
                "suggest_actions":      data.get("suggest_actions", []),
                "future_plan":          data.get("future_plan", []),
                "messages":             [HumanMessage(content=summary)],
            }}
        except Exception as e:
            return {{
                "category": "General HR", "sentiment_score": 0.5, "empathy_score": 0.5,
                "tone_flags": [], "keywords": [], "strengths": [], "improvement_areas": [],
                "consultation_overview": "", "improvements": [], "suggest_actions": [], "future_plan": [],
                "messages": [HumanMessage(content=f"Analysis failed: {{e}}. Please re-share the transcript.")],
            }}

    # ── System Prompt ───────────────────────────────────
    sys_msg = """You are a professional HR performance coach.

TOOLS AVAILABLE:
1. python_repl — use to create a simple bar chart of sentiment and empathy scores
2. pdf_tool_node — use to generate the final PDF report with FLAT parameters only

STRICT TOOL CALLING RULES for pdf_tool_node:
- Every parameter must be a plain string or a list of plain strings
- consultation_overview → plain text string
- improvements → list of strings
- suggest_actions → list of strings
- future_plan → list of strings like "Book Title by Author"
- DO NOT pass any nested dict or object as any parameter value

WORKFLOW after transcript analysis is complete:
Step 1 → Call python_repl to visualize scores
Step 2 → Call pdf_tool_node with flat parameters to generate report

BOUNDARIES:
- Only discuss HR performance and coaching topics
- Never skip PDF generation
- Never give feedback without the transcript"""

    # ── Agent Node ──────────────────────────────────────
    def agent_node(state: HRState):
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_msg),
            ("placeholder", "{messages}")
        ])
        agent    = prompt | llm.bind_tools(tools)
        messages = state.get("messages", [])
        response = agent.invoke({"messages": messages})

        # ── PATCH: serialize coaching_guide_report to string BEFORE
        #    Anthropic API validates the tool call schema.
        #    The LLM sometimes returns it as a dict even though type is str.
        if hasattr(response, "tool_calls") and response.tool_calls:
            patched_calls = []
            for tc in response.tool_calls:
                if tc.get("name") == "pdf_tool_node":
                    args = dict(tc.get("args", {}))
                    cgr = args.get("coaching_guide_report")
                    if isinstance(cgr, dict):
                        args["coaching_guide_report"] = json.dumps(cgr)
                    elif cgr is not None and not isinstance(cgr, str):
                        args["coaching_guide_report"] = str(cgr)
                    patched_calls.append({**tc, "args": args})
                else:
                    patched_calls.append(tc)
            response.tool_calls = patched_calls

        return {"messages": [response]}

    # ── Tool Node ───────────────────────────────────────
    def tool_node_fn(state: HRState):
        messages     = state.get("messages", [])
        last_message = messages[-1] if messages else None
        if not last_message or not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return {}
        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = dict(tool_call["args"])
            result = None
            for t in tools:
                if t.name == tool_name:
                    try:
                        result = t.invoke(tool_args)
                    except Exception as e:
                        result = f"Tool error: {str(e)}"
                    break
            if result is None:
                result = f"Tool \'{tool_name}\' not found."
            tool_messages.append({"role": "tool", "content": str(result), "tool_call_id": tool_call["id"]})
        return {"messages": tool_messages}

    # ── Filter Messages ─────────────────────────────────
    def filter_message(state: HRState):
        messages = state.get("messages", [])
        if len(messages) > 20:
            return {"messages": [RemoveMessage(id=m.id) for m in messages[:-20]]}
        return {}

    # ── Routing ─────────────────────────────────────────
    def should_continue(state: HRState):
        messages     = state.get("messages", [])
        last_message = messages[-1] if messages else None
        if not last_message:
            return "end"
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # ── Compile Graph ────────────────────────────────────
    memory   = MemorySaver()
    workflow = StateGraph(HRState)
    workflow.add_node("filter_messages",    filter_message)
    workflow.add_node("analyze_transcript", analyze_transcript)
    workflow.add_node("agent",              agent_node)
    workflow.add_node("tools",              tool_node_fn)
    workflow.add_edge(START,                "filter_messages")
    workflow.add_edge("filter_messages",    "analyze_transcript")
    workflow.add_edge("analyze_transcript", "agent")
    workflow.add_edge("tools",              "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    return workflow.compile(checkpointer=memory)

# ── Session State Init ─────────────────────────────────
if "messages_display" not in st.session_state:
    st.session_state.messages_display = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "hr-session-001"
if "llm_ready" not in st.session_state:
    st.session_state.llm_ready = False
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = "HR_Report.pdf"
if "hr_name" not in st.session_state:
    st.session_state.hr_name = ""
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None


# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
        <div style="font-family:'DM Serif Display',serif; font-size:1.4rem; color:#c8d0dc;">🎯 HR Coach</div>
        <div style="font-size:0.75rem; color:#4a5568; letter-spacing:1px; text-transform:uppercase;">Agent Configuration</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">LLM Provider</div>', unsafe_allow_html=True)
    provider = st.selectbox("", list(PROVIDER_MODELS.keys()), label_visibility="collapsed")
    model = st.selectbox("Model", PROVIDER_MODELS[provider], label_visibility="visible")
    api_key = st.text_input("🔑 API Key", type="password", placeholder="Enter your API key...")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Session Info</div>', unsafe_allow_html=True)
    hr_name_input = st.text_input("HR Name", placeholder="e.g. Sarah Johnson", value=st.session_state.hr_name)
    if hr_name_input:
        st.session_state.hr_name = hr_name_input
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚀 Initialize Agent", use_container_width=True):
        if not api_key:
            st.error("Please enter your API key.")
        else:
            with st.spinner("Building agent..."):
                try:
                    llm = get_llm(provider, api_key, model)
                    st.session_state.agent = build_agent(llm)
                    st.session_state.llm_ready = True
                    st.session_state.messages_display = []
                    st.session_state.pdf_bytes = None
                    # Greet the HR
                    name = st.session_state.hr_name or "there"
                    greeting = f"Hello {name}! 👋 I'm your HR Performance Coach. I'm here to help you reflect on your HR conversations and grow your skills.\n\nPlease share the full transcript of your HR call below, along with the call duration, and I'll analyze it comprehensively for you."
                    st.session_state.messages_display.append({"role": "assistant", "content": greeting})
                    st.success(f"✅ Agent ready using {provider} / {model}")
                except Exception as e:
                    st.error(f"Failed to initialize: {e}")

    st.markdown("---")

    if st.session_state.llm_ready:
        st.markdown(f"""
        <div style="padding:0.8rem; background:rgba(72,187,120,0.08); border:1px solid rgba(72,187,120,0.2); border-radius:10px; text-align:center;">
            <div style="color:#48bb78; font-size:0.78rem; font-weight:600;">● AGENT ACTIVE</div>
            <div style="color:#4a5568; font-size:0.72rem; margin-top:0.3rem;">{provider} · {model}</div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.pdf_bytes:
        st.markdown("---")
        st.download_button(
            label="📥 Download PDF Report",
            data=st.session_state.pdf_bytes,
            file_name=st.session_state.pdf_filename,
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.72rem; color:#3a4058; text-align:center; line-height:1.6;">
        <b style="color:#4a5568;">Supported Providers</b><br>
        OpenAI · Anthropic · Groq · OpenRouter<br><br>
        Your API key is never stored.<br>
        Used only for this session.
    </div>
    """, unsafe_allow_html=True)


# ── Main Content ───────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1><span class="accent-dot"></span>HR Coaching Agent</h1>
    <p>AI-powered HR performance analysis · Sentiment · Empathy · Coaching guidance · PDF reports</p>
</div>
""", unsafe_allow_html=True)

# Not initialized
if not st.session_state.llm_ready:
    st.markdown("""
    <div class="info-box">
        👈 <b>Configure your agent in the sidebar</b> — choose a provider, enter your API key, set the HR name, then click <b>Initialize Agent</b> to begin.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    for col, provider_name, color, desc in [
        (col1, "OpenAI", "#63b3ed", "GPT-4o, GPT-4 Turbo"),
        (col2, "Anthropic", "#9a75ea", "Claude Opus, Sonnet"),
        (col3, "Groq", "#48bb78", "Llama 3.3, Mixtral"),
        (col4, "OpenRouter", "#f6ad55", "Multi-model gateway"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-color: rgba({color.replace('#','')},0.2);">
                <div style="font-size:1.5rem; margin-bottom:0.5rem;">{"🟦" if provider_name=="OpenAI" else "🟣" if provider_name=="Anthropic" else "🟢" if provider_name=="Groq" else "🟠"}</div>
                <div style="font-weight:600; color:#c8d0dc; font-size:0.9rem;">{provider_name}</div>
                <div style="font-size:0.72rem; color:#4a5568; margin-top:0.3rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <br>
    <div class="section-header">How it works</div>
    """, unsafe_allow_html=True)
    steps = [
        ("1", "Configure", "Select your LLM provider, model, and enter your API key in the sidebar."),
        ("2", "Initialize", "Click 'Initialize Agent' to boot up the HR coaching graph."),
        ("3", "Paste Transcript", "Share the HR call transcript and duration in the chat."),
        ("4", "Get Report", "Receive analysis, scores, coaching guide and a downloadable PDF."),
    ]
    cols = st.columns(4)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div style="background:#141824; border:1px solid #1e2535; border-radius:12px; padding:1.2rem; height:100%;">
                <div style="font-family:'DM Serif Display',serif; font-size:2rem; color:#2a3a55; line-height:1;">{num}</div>
                <div style="font-weight:600; color:#c8d0dc; font-size:0.9rem; margin: 0.5rem 0 0.3rem 0;">{title}</div>
                <div style="font-size:0.8rem; color:#4a5568; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# Initialized — show chat
else:
    # Chat history
    for msg in st.session_state.messages_display:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f"""
            <div class="msg-user">
                <div class="msg-label">You</div>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-assistant">
                <div class="msg-label">🎯 HR Coach Agent</div>
                {content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

    # Show analysis dashboard if available
    if st.session_state.analysis_data:
        d = st.session_state.analysis_data
        st.markdown('<div class="section-header">📊 Analysis Dashboard</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{d.get('sentiment_score', 0):.2f}</div>
                <div class="metric-label">Sentiment Score</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{d.get('empathy_score', 0):.2f}</div>
                <div class="metric-label">Empathy Score</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-family:'DM Serif Display',serif; font-size:1.1rem; color:#63b3ed; margin-bottom:0.3rem;">{d.get('category','—')}</div>
                <div class="metric-label">Category</div>
            </div>
            """, unsafe_allow_html=True)

        if d.get("tone_flags"):
            st.markdown("**Tone Flags**")
            pills = "".join([f'<span class="badge badge-purple">{f}</span>' for f in d["tone_flags"]])
            st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)

        if d.get("keywords"):
            st.markdown("**Keywords**")
            pills = "".join([f'<span class="badge badge-blue">{k}</span>' for k in d["keywords"]])
            st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)

        col_s, col_i = st.columns(2)
        with col_s:
            if d.get("strengths"):
                st.markdown("**✅ Strengths**")
                for s in d["strengths"]:
                    st.markdown(f'<span class="badge badge-green">• {s}</span><br>', unsafe_allow_html=True)
        with col_i:
            if d.get("improvement_areas"):
                st.markdown("**⚡ Improvement Areas**")
                for item in d["improvement_areas"]:
                    st.markdown(f'<span class="badge badge-amber">• {item}</span><br>', unsafe_allow_html=True)

    st.markdown("---")

    # Input
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_area(
            "Message",
            placeholder="Type your message or paste the HR call transcript here...",
            height=100,
            label_visibility="collapsed",
            key="user_input"
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        send_clicked = st.button("Send →", use_container_width=True)

    if send_clicked and user_input.strip():
        st.session_state.messages_display.append({"role": "user", "content": user_input})

        with st.spinner("🎯 Analyzing..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                from langchain_core.messages import HumanMessage
                inputs = {
                    "messages": [HumanMessage(content=user_input)],
                    "hr_name": st.session_state.hr_name,
                    "transcript": user_input,
                    "duration": "",
                    "category": "",
                    "sentiment_score": 0.5,
                    "empathy_score": 0.5,
                    "tone_flags": [],
                    "keywords": [],
                    "strengths": [],
                    "improvement_areas": [],
                    "consultation_overview": "",
                    "improvements": [],
                    "suggest_actions": [],
                    "future_plan": [],
                    "pdf_bytes": None,
                }
                result = st.session_state.agent.invoke(inputs, config=config)
                messages_out = result.get("messages", [])
                last_ai = None
                for m in reversed(messages_out):
                    if hasattr(m, "content") and not hasattr(m, "tool_calls"):
                        if m.__class__.__name__ in ["AIMessage", "ChatMessage"] or (hasattr(m, "type") and m.type == "ai"):
                            last_ai = m.content
                            break
                    if hasattr(m, "content") and m.__class__.__name__ == "AIMessage":
                        last_ai = m.content
                        break

                if not last_ai:
                    for m in reversed(messages_out):
                        if hasattr(m, "content") and isinstance(m.content, str) and len(m.content) > 10:
                            last_ai = m.content
                            break

                if last_ai:
                    st.session_state.messages_display.append({"role": "assistant", "content": last_ai})

                # Store analysis data for dashboard
                for key in ["sentiment_score", "empathy_score", "category", "tone_flags", "keywords",
                            "strengths", "improvement_areas", "consultation_overview",
                            "improvements", "suggest_actions", "future_plan"]:
                    val = result.get(key)
                    if val:
                        if st.session_state.analysis_data is None:
                            st.session_state.analysis_data = {}
                        st.session_state.analysis_data[key] = val

            except Exception as e:
                st.session_state.messages_display.append({
                    "role": "assistant",
                    "content": f"⚠️ Error processing your request: {str(e)}\n\nPlease check your API key and try again."
                })

        st.rerun()

    # PDF download reminder
    if st.session_state.pdf_bytes:
        st.markdown("""
        <div class="info-box" style="margin-top:1rem;">
            📥 <b>Your PDF report is ready!</b> Click <b>"Download PDF Report"</b> in the sidebar to save it.
        </div>
        """, unsafe_allow_html=True)
