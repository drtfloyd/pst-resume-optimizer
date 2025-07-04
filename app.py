from psa_license.license import get_user_mode
import streamlit as st

from PyPDF2 import PdfReader
import string
from io import BytesIO
import zipfile
import re
import json
import os
import pandas as pd
import asyncio

# --- Custom CSS for a Polished Look ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
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
    .stFileUploader {
        border: 2px dashed #bdc3c7;
        border-radius: 8px;
        padding: 20px;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

if "license_key" not in st.session_state:
    st.session_state["license_key"] = ""

license_input = st.sidebar.text_input(
    "Enter your PSA™ License Key",
    value=st.session_state["license_key"],
    type="password"
)

if license_input != st.session_state["license_key"]:
    st.session_state["license_key"] = license_input

current_license_tier = get_user_mode(st.session_state["license_key"])

if current_license_tier in ["pro", "enterprise"]:
    st.success("✅ Pro License Verified!")
elif current_license_tier == "freemium":
    st.info("🟢 Freemium access granted. Upgrade for more features.")
else:
    st.warning("🔒 Enter your PSA™ License Key to continue.")

@st.cache_data(show_spinner="Loading keyword ontology...")
def load_ontology(ontology_path="ontology.json"):
    if not os.path.exists(ontology_path):
        st.error(f"FATAL: Ontology file not found at '{ontology_path}'.")
        return None
    try:
        with open(ontology_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        st.error(f"FATAL: Could not read or parse ontology file: {e}")
        return None

def extract_text_from_file(file):
    if file is None: return ""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            return file.getvalue().decode("utf-8")
    except Exception as e:
        st.warning(f"⚠️ Failed to extract text: {e}"); return ""

def clean_and_extract_words(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text).lower()
    text = re.sub(r'https?://\S+|\S+@\S+', '', text)
    text = re.sub(f'[{re.escape(string.punctuation)}0-9]', '', text)
    return {word for word in text.split() if len(word) > 2}

def run_ontological_analysis(resume_file, jd_file, ontology):
    resume_text = extract_text_from_file(resume_file)
    jd_text = extract_text_from_file(jd_file)
    if not resume_text or not jd_text: return None

    resume_words = clean_and_extract_words(resume_text)
    jd_words = clean_and_extract_words(jd_text)

    signal_domains = ontology.get("SignalDomains", {})
    soc_groups = ontology.get("SOC_Groups", {})

    best_soc_group, max_soc_score = None, -1
    for group_name, group_data in soc_groups.items():
        group_keywords = {kw for domain in group_data.get("signal_domains", []) for phrase in signal_domains.get(domain, []) for kw in phrase.lower().split()}
        score = len(jd_words.intersection(group_keywords))
        if score > max_soc_score: max_soc_score, best_soc_group = score, group_name

    domain_scores, domain_gaps, all_jd_keywords = {}, {}, set()
    for domain_name, keywords in signal_domains.items():
        domain_keywords = {kw for phrase in keywords for kw in phrase.lower().split()}
        total_in_domain_from_jd = domain_keywords.intersection(jd_words)
        if not total_in_domain_from_jd: continue
        all_jd_keywords.update(total_in_domain_from_jd)
        matched_in_domain = total_in_domain_from_jd.intersection(resume_words)
        domain_scores[domain_name] = (len(matched_in_domain) / len(total_in_domain_from_jd)) * 100
        if gaps := total_in_domain_from_jd - resume_words: domain_gaps[domain_name] = sorted(list(gaps))

    overall_score = (len(all_jd_keywords.intersection(resume_words)) / len(all_jd_keywords)) * 100 if all_jd_keywords else 0

    return {
        "predicted_soc_group": best_soc_group,
        "critical_domains": soc_groups.get(best_soc_group, {}).get("signal_domains", []),
        "domain_scores": domain_scores,
        "domain_gaps": domain_gaps,
        "overall_score": overall_score,
        "resume_text": resume_text,
        "jd_text": jd_text
    }

# --- Handwritten Cover Letter Fallback ---
def fallback_cover_letter(resume_text, jd_text, gaps):
    name = "[Your Name]"
    company = "[Company Name]"
    role = "[Job Title]"
    top_missing = list({word for sub in gaps.values() for word in sub})[:5]
    gaps_formatted = ", ".join(top_missing) if top_missing else "the key skills outlined"

    letter = f"""
Dear Hiring Team at {company},

I am writing to express my interest in the {role} position at your organization. With a background that aligns with your job description and a passion for continuous growth, I believe I bring the necessary qualifications and motivation to succeed in this role.

While reviewing your job description, I noticed an emphasis on competencies such as {gaps_formatted}. I am currently sharpening my expertise in these areas and am eager to bring this learning mindset to your team.

Enclosed is my resume for your consideration. I welcome the opportunity to further discuss how I can contribute to your goals.

Thank you for your time and consideration.

Sincerely,
{name}
"""
    return letter

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
                    st.session_state.analysis_results = run_ontological_analysis(st.session_state.resume_file, st.session_state.jd_file, ontology)
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
    tab1, tab2, tab3 = st.tabs(["📊 Strategic Scorecard", "🔑 Gap Analysis", "🤖 AI Content Studio"])

    with tab1:
        st.header("📋 Analysis Summary")
        st.metric(label="Overall Resume Match Score", value=f"{results['overall_score']:.1f}%", help="This score represents the overall percentage of relevant keywords from the job description that were found in your resume.")
        st.progress(int(results['overall_score']))

        st.subheader("Predicted Job Category")
        soc_group = results['predicted_soc_group']
        st.info(f"**{soc_group}**" if soc_group else "Could not determine job category.")

        st.subheader("Your Signal Domain Scores")
        st.caption("This shows your alignment with key competency areas. Focus on improving the 'Critical' domains for this role.")

        critical_domains = set(results['critical_domains'])
        domain_scores = results['domain_scores']

        for domain, score in sorted(domain_scores.items(), key=lambda item: item[1], reverse=True):
            if domain in critical_domains:
                st.markdown(f"**{domain} (Critical)**")
            else:
                st.markdown(f"{domain}")
            st.progress(int(score))

    with tab2:
        st.header("Keyword Gap Analysis")
        st.info("This shows important keywords from the job description that are missing from your resume, grouped by their strategic domain.")

        domain_gaps = results['domain_gaps']
        sorted_domains = sorted(domain_gaps.keys(), key=lambda d: d not in critical_domains)

        for domain in sorted_domains:
            is_critical = " (Critical for this role)" if domain in critical_domains else ""
            with st.expander(f"🚨 {domain}{is_critical} - {len(domain_gaps[domain])} Gaps"):
                st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 5px;'>" + "".join([f"<span style='background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;'>{word}</span>" for word in domain_gaps[domain]]) + "</div>", unsafe_allow_html=True)

    with tab3:
        st.header("AI Content Studio (Fallback Mode)")

        st.subheader("✉️ Cover Letter Generator")
        if st.button("Generate Cover Letter"):
            st.session_state.cover_letter = fallback_cover_letter(results['resume_text'], results['jd_text'], results['domain_gaps'])
        if 'cover_letter' in st.session_state:
            st.text_area("Generated Cover Letter:", value=st.session_state.cover_letter, height=300)
