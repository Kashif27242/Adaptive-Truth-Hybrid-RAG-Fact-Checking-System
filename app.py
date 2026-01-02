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
    """Injects custom CSS for a polished, dark-themed UI."""
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a; color: #f8fafc; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #1e293b; color: #f8fafc; border-color: #334155;
        }
        .status-badge {
            font-weight: bold; padding: 0.5rem 1.5rem; border-radius: 99px;
            text-transform: uppercase; font-size: 1.2rem; display: inline-block;
        }
        .status-supported { color: #34d399; border: 2px solid #34d399; background: rgba(52, 211, 153, 0.1); }
        .status-refuted { color: #f87171; border: 2px solid #f87171; background: rgba(248, 113, 113, 0.1); }
        .status-info { color: #fbbf24; border: 2px solid #fbbf24; background: rgba(251, 191, 36, 0.1); }
        .evidence-card {
            background: #1e293b; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;
            border-left: 4px solid #3b82f6;
        }
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
