import streamlit as st
import json
import io
import operator
import matplotlib.pyplot as plt
import re
from typing import TypedDict, List, Optional, Annotated
from pydantic import BaseModel, Field

# LangChain & LangGraph Imports
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- Page Config ---
st.set_page_config(page_title="HR Coach Agent", layout="wide", page_icon="")

# --- YOUR ORIGINAL PROMPTS (With Strict JSON Enforcement Added) ---

analyze_prompt_template = """You are an expert HR coach analyst.
Analyze the given HR call transcript and extract detailed insights.
Return a JSON object with exactly these fields. Use clear short sentence explanations for each strength, improvement, and coaching point.

{{
    "category": "MUST be exactly one of these five options only: Onboarding / Performance Review / Grievance / Exit Interview / General HR",
    "sentiment_score": <float between 0.0 to 1.0>,
    "empathy_score": <float between 0.0 to 1.0>,
    "tone_flags": ["List 4-5 specific tone observations"],
    "keywords": ["Extract 8-10 important keywords"],
    "strengths": ["List 3 strengths. For each, include a short explanation/evidence sentence."],
    "improvement_areas": ["List 3 improvement areas with 'Missing' + 'Should have said' and short coaching notes."],
    "coaching_guide_report": {{
       "consulation_overview": "Short summary",
       "improvements": ["3 detailed explanation statements"],
       "suggest_actions": ["4 concrete actions"],
       "future_plan": ["3 books/articles with short rationale"]
    }}
}}

Important output rules:
- Return ONLY valid JSON with no markdown formatting.
- Do NOT include any extra fields.
- For each strength and improvement, include a brief explanation sentence.
- In coaching_guide_report, include a concise plan line for each item.

CRITICAL INSTRUCTIONS FOR TOOL CALLING:
1. After analyzing, you MUST call 'create_visualization_code' with the scores.
2. Then, you MUST call 'generate_pdf_report'.
3. For the 'coaching_guide' argument in the PDF tool:
   - You MUST provide a VALID JSON STRING.
   - Do NOT write plain text like "The consultation...".
   - Do NOT include markdown code blocks (```json).
   - It must look exactly like: "{{\"consulation_overview\": \"...\", \"improvements\": [...]}}"
"""

sys_msg = """
<role>
You are a Guiding Partner of Human Resources.
</role>
<tone>
Professional, Empathetic, and Constructive.
</tone>
<task>
1) Analyze transcript.
2) Call 'create_visualization_code'.
3) Call 'generate_pdf_report' with valid JSON strings for complex fields.
</task>
<boundaries>
- NEVER skip PDF generation.
- Ensure all tool arguments are valid types (strings, floats, or JSON strings).
</boundaries>
"""

# --- Sidebar ---
st.sidebar.title("⚙️ Configuration")
provider = st.sidebar.selectbox("Provider", ["OpenAI", "Groq", "Google Gemini", "xAI (Grok)"])
api_key = st.sidebar.text_input(f"{provider} API Key", type="password")

model_mapping = {
    "OpenAI": "gpt-4o-mini",
    "Groq": "llama-3.3-70b-versatile",
    "Google Gemini": "gemini-1.5-flash",
    "xAI (Grok)": "grok-beta"
}
selected_model_name = st.sidebar.selectbox("Model", list(model_mapping.keys()))
actual_model = model_mapping[selected_model_name]

if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None

# --- Helper: Get LLM ---
def get_llm(provider, key, model):
    if not key: return None
    try:
        if provider == "OpenAI":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(api_key=key, model=model, temperature=0)
        elif provider == "Groq":
            from langchain_groq import ChatGroq
            return ChatGroq(api_key=key, model=model, temperature=0)
        elif provider == "Google Gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(api_key=key, model=model, temperature=0)
        elif provider == "xAI (Grok)":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(api_key=key, model=model, base_url="https://api.x.ai/v1", temperature=0)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- Tools ---

@tool
def create_visualization_code(sentiment: float, empathy: float) -> str:
    """Generates python code for a bar chart. Returns confirmation."""
    return f"CHART_CODE_GENERATED: Sentiment={sentiment}, Empathy={empathy}"

@tool
def generate_pdf_report(
    hr_name: str,
    category: str,
    sentiment_score: float,
    empathy_score: float,
    tone_flags: List[str] | str,
    keywords: List[str] | str,
    strengths: List[str] | str,
    improvement_areas: List[str] | str,
    coaching_guide: str  # Expecting a JSON STRING here
) -> str:
    """
    Generates the final PDF report.
    ARGUMENT REQUIREMENT: 'coaching_guide' MUST be a valid JSON string representing the guide object.
    Do not pass plain text.
    """
    normalized = lambda v: "\n".join(v) if isinstance(v, list) else v
    payload = {
        "hr_name": hr_name,
        "category": category,
        "sentiment_score": sentiment_score,
        "empathy_score": empathy_score,
        "tone_flags": normalized(tone_flags),
        "keywords": normalized(keywords),
        "strengths": normalized(strengths),
        "improvement_areas": normalized(improvement_areas),
        "coaching_guide": coaching_guide
    }
    return f"PDF_READY:{json.dumps(payload)}"

tools = [create_visualization_code, generate_pdf_report]

# --- Graph State ---
class HRState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    hr_name: str
    transcript: str

# --- Nodes ---

def agent_node(state: HRState):
    llm = st.session_state.get('current_llm')
    if not llm:
        return {"messages": [HumanMessage(content="Error: LLM not initialized")] }
    
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        ("human", analyze_prompt_template),
        ("human", "HR Name: {hr_name}\nTranscript: {transcript}"),
        MessagesPlaceholder(variable_name="messages", optional=True)
    ])
    
    chain = prompt | llm_with_tools
    inputs = {
        "hr_name": state["hr_name"],
        "transcript": state["transcript"],
        "messages": state["messages"]
    }
    response = chain.invoke(inputs)
    return {"messages": [response]}

def tool_node(state: HRState):
    node = ToolNode(tools)
    return node.invoke(state)

def should_continue(state: HRState) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"

# Build Graph
workflow = StateGraph(HRState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")
app_graph = workflow.compile()

# --- Helper: Robust JSON Parser & PDF Generator ---
def safe_json_loads(json_str: str):
    """Cleans markdown fences and attempts to parse JSON."""
    if not json_str:
        return {}
    
    # Remove markdown code blocks if present
    cleaned = re.sub(r'^```json\s*', '', json_str)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: If it's just plain text (the error case you saw), wrap it
        # But ideally, the prompt prevents this.
        return {"consulation_overview": cleaned, "improvements": [], "suggest_actions": [], "future_plan": []}

def create_pdf_in_main_thread(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("HR Coaching Guide Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>HR Name:</b> {data.get('hr_name', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Category:</b> {data.get('category', 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    s_score = float(data.get('sentiment_score', 0))
    e_score = float(data.get('empathy_score', 0))
    story.append(Paragraph(f"<b>Sentiment:</b> {s_score:.2f} | <b>Empathy:</b> {e_score:.2f}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    
    sections = [
        ("Strengths", data.get('strengths', '')),
        ("Improvement Areas", data.get('improvement_areas', '')),
        ("Tone Flags", data.get('tone_flags', '')),
        ("Keywords", data.get('keywords', ''))
    ]
    
    for title, content in sections:
        story.append(Paragraph(title, styles["Heading2"]))
        if content:
            items = content.split('\n')
            for item in items:
                if item.strip():
                    story.append(Paragraph(f"• {item.strip()}", styles["BodyText"]))
        else:
            story.append(Paragraph("N/A", styles["BodyText"]))
        story.append(Spacer(1, 12))

    story.append(Paragraph("Coaching Plan", styles["Heading2"]))
    
    # ROBUST PARSING HERE
    raw_guide = data.get('coaching_guide', '{}')
    guide_data = safe_json_loads(raw_guide)
    
    if guide_data:
        overview = guide_data.get("consulation_overview", "")
        if overview:
            story.append(Paragraph("<b>Overview:</b>", styles["Heading3"]))
            story.append(Paragraph(overview, styles["BodyText"]))
            story.append(Spacer(1, 6))
            
        for key, label in [("improvements", "Key Improvements"), ("suggest_actions", "Suggested Actions"), ("future_plan", "Future Learning")]:
            items = guide_data.get(key, [])
            if items:
                story.append(Paragraph(f"<b>{label}:</b>", styles["Heading3"]))
                for i, item in enumerate(items, 1):
                    story.append(Paragraph(f"{i}. {item}", styles["BodyText"]))
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No detailed coaching plan generated.", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Main UI ---
st.header("Agent-Based HR Coaching Analysis")
st.write("Agent is connected with 2 tools named Visualization Tool to generate chart code and PDF Report Generator to create a detailed report. The agent will analyze the transcript, generate insights, create a visualization, and produce a PDF report with coaching recommendations.")
hr_name_input = st.text_input("HR Name", value="Salil Shekhar")
transcript_input = st.text_area("Transcript", height=200, placeholder="HR: Hello...")

if st.button("🚀 Run Analysis"):
    if not api_key:
        st.warning("Enter API Key.")
    elif not transcript_input:
        st.warning("Enter Transcript.")
    else:
        llm_instance = get_llm(provider, api_key, actual_model)
        if llm_instance:
            st.session_state['current_llm'] = llm_instance
            st.session_state.pdf_buffer = None 
            st.session_state.extracted_data = None 
            
            with st.spinner("Agent is analyzing..."):
                initial_state = {
                    "messages": [],
                    "hr_name": hr_name_input,
                    "transcript": transcript_input
                }
                
                try:
                    final_state = app_graph.invoke(initial_state)
                    messages = final_state.get("messages", [])
                    
                    pdf_payload = None
                    chart_scores = {}
                    
                    for msg in messages:
                        if isinstance(msg, ToolMessage):
                            content = msg.content
                            if content.startswith("PDF_READY:"):
                                json_str = content.replace("PDF_READY:", "")
                                pdf_payload = json.loads(json_str)
                            if "CHART_CODE_GENERATED" in content:
                                nums = re.findall(r"\d+\.\d+", content)
                                if len(nums) >= 2:
                                    chart_scores = {'s': float(nums[0]), 'e': float(nums[1])}
                    
                    if not pdf_payload:
                        # Fallback: If the agent returned plain JSON in the AI message, parse it and generate PDF.
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                ai_text = msg.content.strip()
                                try:
                                    parsed = json.loads(ai_text)
                                    required_keys = {"category", "sentiment_score", "empathy_score", "tone_flags", "keywords", "strengths", "improvement_areas", "coaching_guide_report"}
                                    if required_keys.issubset(set(parsed.keys())):
                                        coaching = parsed.get("coaching_guide_report", {})
                                        coaching_json = json.dumps(coaching)
                                        pdf_payload = {
                                            "hr_name": hr_name_input,
                                            "category": parsed.get("category", "N/A"),
                                            "sentiment_score": float(parsed.get("sentiment_score", 0)),
                                            "empathy_score": float(parsed.get("empathy_score", 0)),
                                            "tone_flags": json.dumps(parsed.get("tone_flags", [])),
                                            "keywords": json.dumps(parsed.get("keywords", [])),
                                            "strengths": json.dumps(parsed.get("strengths", [])),
                                            "improvement_areas": json.dumps(parsed.get("improvement_areas", [])),
                                            "coaching_guide": coaching_json
                                        }
                                        break
                                except Exception:
                                    continue

                    if pdf_payload:
                        st.session_state.pdf_buffer = create_pdf_in_main_thread(pdf_payload)
                        st.session_state.extracted_data = pdf_payload
                        st.success("Analysis Complete!")
                    else:
                        st.error("PDF tool did not return expected data.")

                    data = st.session_state.extracted_data
                    
                    if data:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Sentiment", f"{float(data.get('sentiment_score', 0)):.2f}")
                        c2.metric("Empathy", f"{float(data.get('empathy_score', 0)):.2f}")
                        c3.metric("Category", data.get('category', 'N/A'))

                        fig, ax = plt.subplots()
                        ax.bar(['Sentiment', 'Empathy'], [float(data.get('sentiment_score', 0)), float(data.get('empathy_score', 0))], color=['#4CAF50', '#2196F3'])
                        ax.set_ylim(0, 1)
                        st.pyplot(fig)

                        with st.expander("View Detailed Analysis", expanded=True):
                            st.write("**Strengths:**")
                            st.write(data.get('strengths', '').replace('\n', '\n- '))
                            st.write("\n**Improvements:**")
                            st.write(data.get('improvement_areas', '').replace('\n', '\n- '))
                            
                            # Display parsed coaching guide nicely
                            raw_guide = data.get('coaching_guide', '')
                            guide_json = safe_json_loads(raw_guide)
                            st.write("\n**Coaching Plan:**")
                            st.json(guide_json)
                        
                        if st.session_state.pdf_buffer:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=st.session_state.pdf_buffer,
                                file_name=f"HR_Report_{hr_name_input}.pdf",
                                mime="application/pdf"
                            )
                    
                    last_ai = next((m.content for m in reversed(messages) if isinstance(m, AIMessage) and not m.tool_calls), "")
                    if last_ai:
                        st.markdown("### 🤖 Agent Summary")
                        st.write(last_ai)

                except Exception as e:
                    st.error(f"Failed: {str(e)}")
                    # Show traceback for debugging
                    import traceback
                    st.code(traceback.format_exc())