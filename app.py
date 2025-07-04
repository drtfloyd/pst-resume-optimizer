import streamlit as st
from PyPDF2 import PdfReader
import string
from io import BytesIO
import zipfile
import re
import json
import os
import pandas as pd

# --- Page & UI Configuration ---
st.set_page_config(
    page_title="PSA™ Resume Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for a Polished Look ---
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Style headers */
    h1, h2, h3 {
        color: #2c3e50; /* Dark blue-gray for a professional look */
    }
    /* Style buttons */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #2c3e50;
        color: #2c3e50;
        background-color: #ffffff;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #3498db;
        color: #ffffff;
        background-color: #3498db;
    }
    .stButton>button:focus {
        box-shadow: 0 0 0 2px #3498db40;
    }
    /* Style file uploader */
    .stFileUploader {
        border: 2px dashed #bdc3c7;
        border-radius: 8px;
        padding: 20px;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)


# --- License Key Utilities ---
def get_user_mode(license_key):
    """Verifies license key against secrets."""
    license_tiers = st.secrets.get("psa", {}).get("license_tiers", {})
    return license_tiers.get(license_key.strip(), None)

# --- Production-Grade Ontology Loader ---
@st.cache_data(show_spinner="Loading keyword ontology...")
def load_ontology(ontology_path="ontology.json"):
    """Loads the full structured ontology from the external JSON file."""
    if not os.path.exists(ontology_path):
        st.error(f"FATAL: Ontology file not found at '{ontology_path}'.")
        return None
    try:
        with open(ontology_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        st.error(f"FATAL: Could not read or parse ontology file: {e}")
        return None

# --- Core Logic Engine ---

def extract_text_from_file(file):
    """Extracts text from an uploaded PDF or TXT file."""
    if file is None:
        return ""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        else: # Assumes txt
            return file.getvalue().decode("utf-8")
    except Exception as e:
        st.warning(f"⚠️ Failed to extract text: {e}")
        return ""

def clean_and_extract_words(text):
    """A helper function to clean text and extract a set of unique words."""
    # Split jumbled words based on case changes (e.g., "wordOne" -> "word One")
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = text.lower()
    text = re.sub(r'https?://\S+|\S+@\S+', '', text)
    text = re.sub(f'[{re.escape(string.punctuation)}0-9]', '', text)
    words = set(text.split())
    # Filter out very short, likely meaningless words
    return {word for word in words if len(word) > 2}

def run_ontological_analysis(resume_file, jd_file, ontology):
    """
    Performs a deep, context-aware analysis using the structured ontology.
    """
    resume_text = extract_text_from_file(resume_file)
    jd_text = extract_text_from_file(jd_file)

    if not resume_text or not jd_text:
        return None

    resume_words = clean_and_extract_words(resume_text)
    jd_words = clean_and_extract_words(jd_text)
    
    signal_domains = ontology.get("SignalDomains", {})
    soc_groups = ontology.get("SOC_Groups", {})

    # 1. Identify the most likely SOC Group from the Job Description
    best_soc_group = None
    max_soc_score = -1
    for group_name, group_data in soc_groups.items():
        group_domains = group_data.get("signal_domains", [])
        group_keywords = set()
        for domain in group_domains:
            for keyword in signal_domains.get(domain, []):
                group_keywords.update(keyword.lower().split())
        
        score = len(jd_words.intersection(group_keywords))
        if score > max_soc_score:
            max_soc_score = score
            best_soc_group = group_name

    # 2. Calculate match scores for each Signal Domain
    domain_scores = {}
    domain_gaps = {}
    all_jd_keywords = set()

    for domain_name, keywords in signal_domains.items():
        domain_keywords = set()
        for keyword in keywords:
            domain_keywords.update(keyword.lower().split())
        
        all_jd_keywords.update(domain_keywords.intersection(jd_words))
        
        matched_in_domain = domain_keywords.intersection(resume_words)
        total_in_domain_from_jd = domain_keywords.intersection(jd_words)
        
        score = (len(matched_in_domain) / len(total_in_domain_from_jd)) * 100 if total_in_domain_from_jd else 0
        domain_scores[domain_name] = score
        
        gaps = total_in_domain_from_jd - resume_words
        if gaps:
            domain_gaps[domain_name] = sorted(list(gaps))

    # 3. Calculate overall match score
    total_matched = len(all_jd_keywords.intersection(resume_words))
    overall_score = (total_matched / len(all_jd_keywords)) * 100 if all_jd_keywords else 0

    return {
        "predicted_soc_group": best_soc_group,
        "critical_domains": soc_groups.get(best_soc_group, {}).get("signal_domains", []),
        "domain_scores": domain_scores,
        "domain_gaps": domain_gaps,
        "overall_score": overall_score
    }

# --- Placeholder functions for other features ---
def generate_cover_letter(): return "Dear Hiring Manager..."
def generate_resume_rebuild(): return ["Optimized bullet point suggesting quantifiable achievements."]
def run_linkedin_optimizer(): return {"Headline Match": "High"}
def export_zip_bundle(resume_file, jd_file):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("resume.pdf", resume_file.getvalue())
        zf.writestr("job_description.txt", jd_file.getvalue())
    return zip_buffer.getvalue()


# --- SIDEBAR UI ---
with st.sidebar:
    st.title("PSA™ Optimizer")
    st.markdown("---")
    st.header("🔐 Access Control")
    license_key = st.text_input("Enter your PSA™ Pro License Key", type="password")
    current_license_tier = get_user_mode(license_key)
    ontology = load_ontology()

    if current_license_tier in ["pro", "enterprise"]:
        st.success("Pro License Verified!")
        st.markdown("---")
        st.header("📂 Upload Documents")
        st.session_state.resume_file = st.file_uploader("Upload your Resume", type=["pdf", "txt"])
        st.session_state.jd_file = st.file_uploader("Upload the Job Description", type=["pdf", "txt"])

        st.markdown("---")
        if st.button("🚀 Analyze Now", use_container_width=True, type="primary"):
            if st.session_state.resume_file and st.session_state.jd_file and ontology:
                with st.spinner("Performing deep ontological analysis..."):
                    st.session_state.analysis_results = run_ontological_analysis(
                        st.session_state.resume_file, st.session_state.jd_file, ontology
                    )
                st.success("Analysis Complete!")
            else:
                st.warning("Please upload both documents to begin.")
    else:
        if license_key: st.error("Invalid License Key.")
        st.info("Enter a valid license key to begin.")
    st.markdown("---")
    st.caption("© PSA™ & AIaPI™ Framework")

# --- MAIN PANEL UI ---
st.title("📄 PSA™ Resume & Career Optimizer")
st.caption("Part of the Presence Signaling Architecture (PSA™) and AI as Presence Interface (AIaPI™) framework.")

if 'analysis_results' not in st.session_state or st.session_state.analysis_results is None:
    st.info("Welcome! Please enter your license key and upload your documents in the sidebar to begin.")
else:
    results = st.session_state.analysis_results
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Scorecard & Summary", "🔑 Keyword Analysis", "📝 Content Generation", "📦 Export Bundle"
    ])

    with tab1:
        st.header("📋 Analysis Summary")
        st.metric(label="Overall Resume Match Score", value=f"{results['overall_score']:.1f}%")
        st.progress(int(results['overall_score']))
        
        st.subheader("Predicted Job Category")
        soc_group = results['predicted_soc_group']
        st.info(f"**{soc_group}**" if soc_group else "Could not determine job category.")
        
        st.subheader("Critical Signal Domains for this Role")
        if results['critical_domains']:
            st.markdown(", ".join([f"`{d}`" for d in results['critical_domains']]))
        
        st.subheader("Your Domain Strengths & Weaknesses")
        domain_scores_df = pd.DataFrame(
            results['domain_scores'].items(),
            columns=['Signal Domain', 'Match Score']
        ).sort_values('Match Score', ascending=False).set_index('Signal Domain')
        st.bar_chart(domain_scores_df)

    with tab2:
        st.header("Gap Analysis by Signal Domain")
        st.info("This shows important keywords from the job description that are missing from your resume, grouped by their strategic domain.")
        
        critical_domains = results['critical_domains']
        domain_gaps = results['domain_gaps']
        
        # Prioritize critical domains first
        sorted_domains = sorted(
            domain_gaps.keys(), 
            key=lambda d: d not in critical_domains
        )
        
        for domain in sorted_domains:
            is_critical = " (Critical for this role)" if domain in critical_domains else ""
            with st.expander(f"🚨 {domain}{is_critical} - {len(domain_gaps[domain])} Gaps"):
                st.markdown(
                    f"<div style='display: flex; flex-wrap: wrap; gap: 5px;'>" +
                    "".join([f"<span style='background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;'>{word}</span>" for word in domain_gaps[domain]]) +
                    "</div>",
                    unsafe_allow_html=True
                )

    with tab3:
        st.header("AI-Powered Content Generation")
        with st.expander("✉️ Generated Cover Letter"):
            st.text_area("Your customized cover letter:", value=generate_cover_letter(), height=300)
        with st.expander("🧠 Optimized Resume Line Suggestions"):
            for line in generate_resume_rebuild():
                st.markdown(f"- {line}")

    with tab4:
        st.header("📦 Create and Download Submission Bundle")
        zip_data = export_zip_bundle(st.session_state.resume_file, st.session_state.jd_file)
        st.download_button("📥 Download ZIP", zip_data, "PSA_Submission_Bundle.zip", "application/zip", use_container_width=True)
