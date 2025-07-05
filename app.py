# --- TRUST & VISIBILITY TUNER ---
def calculate_trust_visibility_scores(results):
    """
    Adds two new metrics based on domain match quality and signal fidelity:
    - Trust Score: Weighted alignment to critical domains
    - Visibility Score: Proxy for presence signal density
    """
    domain_scores = results.get("domain_scores", {})
    critical_domains = set(results.get("critical_domains", []))
    domain_gaps = results.get("domain_gaps", {})

    trust_total, trust_count = 0, 0
    visibility_hits, visibility_total = 0, 0

    for domain, score in domain_scores.items():
        if domain in critical_domains:
            trust_total += score
            trust_count += 1
        if domain in domain_gaps:
            visibility_total += len(domain_gaps[domain]) + 1
            visibility_hits += 1 if score > 40 else 0

    trust_score = trust_total / trust_count if trust_count else 0
    visibility_score = (visibility_hits / visibility_total) * 100 if visibility_total else 0

    return round(trust_score, 1), round(visibility_score, 1)

def generate_hyperprompt(results):
    soc_group = results.get("predicted_soc_group", "[unknown role]")
    critical_domains = results.get("critical_domains", [])
    # Correctly list matched terms from critical domains only
    matched_terms_in_critical_domains = set()
    for domain in critical_domains:
        if domain in results.get('domain_scores', {}):
             # This assumes domain_gaps and domain_scores are aligned, need to find the source keywords
             # For this example, we'll just use the domain names as a proxy for terms
             matched_terms_in_critical_domains.add(domain)


    prompt = f"You are optimizing for a role in {soc_group}. Your presence signal contains strengths in: {', '.join(critical_domains)}. Use terms related to these domains. Keep your voice and presence intact."

    return prompt

from psa_license.license import get_user_mode
import streamlit as st
from PyPDF2 import PdfReader
import string
from io import BytesIO
import re
import json
import os

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
    suggested_titles = soc_groups.get(best_soc_group, {}).get("example_titles", [])

    return {
        "predicted_soc_group": best_soc_group,
        "critical_domains": soc_groups.get(best_soc_group, {}).get("signal_domains", []),
        "domain_scores": domain_scores,
        "domain_gaps": domain_gaps,
        "overall_score": overall_score,
        "resume_text": resume_text,
        "jd_text": jd_text,
        "suggested_titles": suggested_titles
    }

# --- SIDEBAR UI ---
with st.sidebar:
    st.title("PSA™ Optimizer")
