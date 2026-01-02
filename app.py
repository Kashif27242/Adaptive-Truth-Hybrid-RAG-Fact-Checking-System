import streamlit as st
import asyncio
import sys
import os
import contextlib
import io
from dotenv import load_dotenv

# --- Configuration & Setup ---
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')

# Add backend to path for internal module resolution
sys.path.append(BACKEND_DIR)
sys.path.append(ROOT_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

# Import Backend Modules
from backend.agent import verify_claim
from backend.ingest import ingest_data
from backend.models import VerificationResult

# Page Layout Configuration
st.set_page_config(
    page_title="Adaptive Truth | Fact Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UI Components ---

def apply_custom_styles():
    """Injects custom CSS for a polished, dark-themed UI with gradients."""
    st.markdown("""
        <style>
        /* Main Background */
        .stApp {
            background: rgb(15,23,42);
            background: linear-gradient(135deg, rgba(15,23,42,1) 0%, rgba(30,58,138,1) 50%, rgba(15,23,42,1) 100%);
            color: #f8fafc;
        }
        
        /* Inputs & Text Areas */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: rgba(30, 41, 59, 0.6); 
            backdrop-filter: blur(10px);
            color: #f8fafc; 
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 10px;
        }
        .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        }

        /* Status Badges */
        .status-badge {
            font-weight: 700; 
            padding: 0.6rem 2rem; 
            border-radius: 99px;
            text-transform: uppercase; 
            letter-spacing: 1px;
            font-size: 1.1rem; 
            display: inline-block;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            backdrop-filter: blur(5px);
        }
        .status-supported { 
            color: #a7f3d0; 
            border: 1px solid #34d399; 
            background: linear-gradient(90deg, rgba(6,78,59,0.6) 0%, rgba(16,185,129,0.3) 100%);
        }
        .status-refuted { 
            color: #fecaca; 
            border: 1px solid #f87171; 
            background: linear-gradient(90deg, rgba(127,29,29,0.6) 0%, rgba(2ef4444,0.3) 100%); 
        }
        .status-info { 
            color: #fde68a; 
            border: 1px solid #fbbf24; 
            background: linear-gradient(90deg, rgba(120,53,15,0.6) 0%, rgba(245,158,11,0.3) 100%);
        }

        /* Evidence Cards (Glassmorphism) */
        .evidence-card {
            background: rgba(30, 41, 59, 0.4);
            padding: 1.2rem; 
            border-radius: 12px; 
            margin-bottom: 0.8rem;
            border: 1px solid rgba(255,255,255,0.05);
            border-left: 4px solid #3b82f6;
            backdrop-filter: blur(5px);
            transition: transform 0.2s ease;
        }
        .evidence-card:hover {
            transform: translateY(-2px);
            background: rgba(30, 41, 59, 0.6);
            border-left-color: #60a5fa;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
            border: none;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            box-shadow: 0 0 20px rgba(37, 99, 235, 0.6);
            transform: scale(1.02);
        }
        
        /* Divider */
        hr { border-color: rgba(148, 163, 184, 0.2); }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renders the sidebar with admin controls."""
    with st.sidebar:
        st.header("⚙️ Admin Controls")
        st.info("Manage the Local Knowledge Base (FEVER Dataset).")
        
        if st.button("🔄 Run Full Ingestion", use_container_width=True, help="Re-ingest ~20k records into ChromaDB"):
            _handle_ingestion()

def _handle_ingestion():
    """Handles the ingestion process and UI feedback."""
    status = st.empty()
    status.info("⏳ Ingesting data... Please wait.")
    
    try:
        # Capture stdout to display logs in UI
        logs_buffer = io.StringIO()
        with contextlib.redirect_stdout(logs_buffer):
            with st.spinner("Processing records..."):
                ingest_data()
        
        status.success("✅ Ingestion Complete!")
        with st.expander("Show Ingestion Logs"):
            st.code(logs_buffer.getvalue())
            
    except Exception as e:
        status.error(f"❌ Ingestion Failed: {e}")

def render_main_interface():
    """Renders the main claim verification interface."""
    st.title("🛡️ Adaptive Truth")
    st.markdown("##### Hybrid RAG Fact-Checking: **Local Knowledge First** → **Web Search Fallback**")
    
    claim = st.text_area("Enter a claim to verify:", height=100, placeholder="e.g. Fox 2000 Pictures released the film Soul Food.")
    
    if st.button("🔍 Verify Claim", type="primary", use_container_width=True):
        if not claim.strip():
            st.warning("⚠️ Please enter a text claim first.")
            return

        _handle_verification(claim)

def _handle_verification(claim: str):
    """Orchestrates the verification process and result rendering."""
    with st.spinner("🤖 Analyzing... (Checking Local DB → Web)"):
        try:
            # Run async agent
            result = asyncio.run(verify_claim(claim))
            _display_result(result)
        except Exception as e:
            st.error(f"An error occurred during verification: {e}")

def _display_result(result: VerificationResult):
    """Visualizes the verification result."""
    st.divider()
    
    # 1. Verdict System
    verdict = result.verdict
    badge_style = "status-info"
    if verdict == "Supported": badge_style = "status-supported"
    elif verdict == "Refuted": badge_style = "status-refuted"
    
    col1, _ = st.columns([1, 2])
    with col1:
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;"><span class="status-badge {badge_style}">{verdict}</span></div>', unsafe_allow_html=True)

    # 2. Reasoning
    st.subheader("📝 AI Analysis")
    st.write(result.reasoning)
    
    # 3. Evidence Sources
    st.subheader("📚 Evidence Used")
    
    has_web = any("web" in e.source.lower() for e in result.evidence)
    source_type = "🌐 Live Web Search" if has_web else "💾 Local Database"
    st.caption(f"Source Strategy: **{source_type}**")
        
    with st.expander("View Source Details"):
        for e in result.evidence:
            st.markdown(f"""
                <div class="evidence-card">
                    <small><b>Source:</b> {e.source} | <b>Confidence:</b> {e.confidence:.2f}</small><br>
                    <i>"{e.text}"</i>
                </div>
            """, unsafe_allow_html=True)
            if hasattr(e, 'url') and e.url:
                st.markdown(f"[🔗 Open Link]({e.url})")

# --- Main Application Flow ---

if __name__ == "__main__":
    apply_custom_styles()
    render_sidebar()
    render_main_interface()
