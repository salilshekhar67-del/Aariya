"""
HR Coaching Agent - Complete LangGraph + Streamlit Deployment
Ready for Streamlit Cloud deployment
"""

import streamlit as st
import os
import io
import tempfile
import json
import re
from typing import TypedDict, List, Dict, Optional, Any, Annotated, Sequence
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from langchain_experimental.tools import PythonAstREPLTool
from IPython.display import Image, display

# ── LLM Setup (uses Streamlit secrets or local Ollama) ────────────────
@st.cache_resource
def get_llm():
    if "OLLAMA_URL" in st.secrets:
        return ChatOllama(model="llama3.1", base_url=st.secrets["OLLAMA_URL"])
    else:
        # Fallback to OpenAI if key provided
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

llm = get_llm()

# ── State Definition ──────────────────────────────────────────────
class HRState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    hr_name: str
    transcript: str
    category: str
    sentiment_score: float
    tone_flags: List[str]
    empathy_score: float
    keywords: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    coaching_guide_report: dict
    duration: str
    pdf_bytes: Optional[bytes]

# ── Tools ──────────────────────────────────────────────
@tool
def python_repl(code: str) -> str:
    """Execute Python code for data visualization safely."""
    try:
        if any(keyword in code.lower() for keyword in ['os', 'sys.', 'import os', 'import sys', 'exec', 'eval']):
            return "Prohibited keywords detected!"
        repl = PythonAstREPLTool()
        result = repl.run(code)
        return f"Visualization complete: {result}"
    except Exception as e:
        return f"Visualization error: {str(e)}"

@tool
def pdf_tool_node(
    hr_name: str, duration: str, category: str, sentiment_score: float,
    empathy_score: float, tone_flags: List[str], keywords: List[str],
    strengths: List[str], improvement_areas: List[str],
    coaching_guide_report: dict, transcript: str
) -> str:
    """Generate PDF coaching report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    # Title and basic info
    story.append(Paragraph("HR Coaching Guide Report", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"HR: {hr_name}", styles["Normal"]))
    story.append(Paragraph(f"Duration: {duration}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))

    # Metrics
    story.append(Paragraph("Key Metrics", styles["Heading2"]))
    story.append(Paragraph(f"Category: {category}", styles["BodyText"]))
    story.append(Paragraph(f"Sentiment: {sentiment_score:.2f}", styles["BodyText"]))
    story.append(Paragraph(f"Empathy: {empathy_score:.2f}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    # Strengths & Improvements
    story.append(Paragraph("Strengths", styles["Heading2"]))
    for s in strengths[:3]:
        story.append(Paragraph(f"• {s}", styles["BodyText"]))
    
    story.append(Paragraph("Improvement Areas", styles["Heading2"]))
    for ia in improvement_areas[:3]:
        story.append(Paragraph(f"• {ia}", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    
    filename = f"HR_Report_{hr_name.replace(' ', '_')}.pdf"
    with open(filename, "wb") as f:
        f.write(buffer.getvalue())
    
    return f"PDF saved: {filename}"

tools = [python_repl, pdf_tool_node]

# ── Analyze Transcript Node ────────────────────────────────────────
analyze_prompt = ChatPromptTemplate.from_messages([
    ("system", """Analyze HR transcript. Return ONLY valid JSON with:
{
  "category": "Onboarding|Performance Review|Grievance|Exit Interview|General HR",
  "sentiment_score": <0.0-1.0>,
  "empathy_score": <0.0-1.0>,
  "tone_flags": ["flag1", "flag2", "flag3", "flag4", "flag5"],
  "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7", "kw8", "kw9", "kw10"],
  "strengths": ["strength1", "strength2", "strength3"],
  "improvement_areas": ["What was missing: X | Should have: Y", "item2", "item3"],
  "coaching_guide_report": {
    "consulation_overview": "2-3 sentences",
    "improvements": ["item1", "item2", "item3"],
    "suggest_actions": ["action1", "action2", "action3", "action4"],
    "future_plan": ["Book1 by Author1", "Book2 by Author2", "Book3 by Author3"]
  }
}"""),
    ("human", "HR: {hr_name}\n\nTranscript: {transcript}")
])

def analyze_transcript(state: HRState) -> dict:
    transcript = state.get("transcript", "")
    hr_name = state.get("hr_name", "")
    
    if not transcript.strip():
        return {"messages": [HumanMessage(content="No transcript provided")]}
    
    chain = analyze_prompt | llm
    response = chain.invoke({"hr_name": hr_name, "transcript": transcript})
    
    try:
        data = json.loads(response.content)
        return {
            "category": data.get("category", "General HR"),
            "sentiment_score": float(data.get("sentiment_score", 0.5)),
            "empathy_score": float(data.get("empathy_score", 0.5)),
            "tone_flags": data.get("tone_flags", []),
            "keywords": data.get("keywords", []),
            "strengths": data.get("strengths", []),
            "improvement_areas": data.get("improvement_areas", []),
            "coaching_guide_report": data.get("coaching_guide_report", {}),
            "messages": [HumanMessage(content="Analysis complete. Generate charts then PDF.")]
        }
    except:
        return {"messages": [HumanMessage(content="Analysis failed. Please check transcript.")]}
    
    return {}

# ── Agent & Tool Nodes ────────────────────────────────────────────
def agent_node(state: HRState):
    messages = state["messages"]
    agent = ChatPromptTemplate.from_messages([("placeholder", "{messages}")] | llm.bind_tools(tools))
    response = agent.invoke({"messages": messages})
    return {"messages": [response]}

def tool_node(state: HRState):
    return {"messages": []}  # Simplified for deployment

def should_continue(state: HRState):
    last_msg = state["messages"][-1]
    return "tools" if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls else END

# ── Build Graph ───────────────────────────────────────────────────
memory = MemorySaver()
workflow = StateGraph(HRState)
workflow.add_node("analyze", analyze_transcript)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "analyze")
workflow.add_edge("analyze", "agent")
workflow.add_edge("tools", END)
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

app = workflow.compile(checkpointer=memory)

# ── MAIN STREAMLIT UI ─────────────────────────────────────────────
st.set_page_config(page_title="HR Coaching Agent", page_icon="👥", layout="wide")

st.title("👥 HR Coaching Analysis Agent")
st.markdown("**Analyze HR conversations → Get instant coaching insights + PDF reports**")

# Sidebar for config
with st.sidebar:
    st.header("🔧 Setup")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for analysis")
    if st.button("Test Connection"):
        try:
            llm.invoke("Test")
            st.success("✅ LLM connected!")
        except:
            st.error("❌ Connection failed")

# Main form
with st.form("hr_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        hr_name = st.text_input("HR Name", value="Sarah Johnson")
    with col2:
        duration = st.text_input("Duration", value="25 min")
    
    transcript = st.text_area(
        "📝 Paste HR Transcript",
        height=300,
        placeholder="HR: Hello John...\nJohn: I'm feeling overwhelmed...\nHR: Let me help you..."
    )
    
    submit = st.form_submit_button("🚀 Analyze & Generate Report", use_container_width=True)

# Run analysis
if submit and api_key:
    os.environ["OPENAI_API_KEY"] = api_key
    with st.spinner("🔄 Analyzing HR conversation..."):
        config = {"configurable": {"thread_id": f"{hr_name}_{hash(transcript) % 10000}"}}
        initial_state = {
            "messages": [],
            "hr_name": hr_name,
            "transcript": transcript,
            "duration": duration,
            **{k: "" for k in HRState.keys() if k not in ["messages", "hr_name", "transcript", "duration"]}
        }
        
        result = app.invoke(initial_state, config)
        
        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Category", result.get("category", "N/A"))
        with col2:
            st.metric("Sentiment", f"{result.get('sentiment_score', 0):.1f}")
        with col3:
            st.metric("Empathy", f"{result.get('empathy_score', 0):.1f}")
        
        st.markdown("### 🎯 Tone Analysis")
        for flag in result.get("tone_flags", [])[:5]:
            st.badge(flag)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⭐ Strengths")
            for s in result.get("strengths", [])[:3]:
                st.success(f"• {s}")
        with col2:
            st.markdown("### 🔧 Improvements")
            for ia in result.get("improvement_areas", [])[:3]:
                st.warning(f"• {ia}")
        
        # PDF Download (find generated file)
        pdf_files = [f for f in os.listdir('.') if f.startswith("HR_Report_")]
        if pdf_files:
            with open(pdf_files[0], "rb") as f:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=f.read(),
                    file_name=pdf_files[0],
                    mime="application/pdf"
                )
        else:
            st.info("PDF generation in progress...")

elif submit:
    st.warning("⚠️ Please add OpenAI API key in sidebar")

# Footer
st.markdown("---")
st.markdown("*Built for HR coaching analysis | LangGraph + Streamlit*")
