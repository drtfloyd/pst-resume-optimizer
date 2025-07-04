import streamlit as st
from PyPDF2 import PdfReader
import string
from io import BytesIO
import zipfile

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
    # Fallback to an empty dict if secrets are not set
    license_tiers = st.secrets.get("psa", {}).get("license_tiers", {})
    return license_tiers.get(license_key.strip(), None)

# --- Backend Placeholder Functions (Your original logic) ---

def extract_pdf_text(file):
    """Extracts text from an uploaded PDF file."""
    if file is None:
        return ""
    try:
        reader = PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        st.warning(f"⚠️ Failed to extract text from PDF: {e}")
        return ""

def generate_signal_table(resume_file, jd_file):
    """Analyzes resume against job description for keyword matching."""
    resume_text = extract_pdf_text(resume_file)
    jd_text = extract_pdf_text(jd_file)

    if not resume_text or not jd_text:
        return {}, 0.0, []

    # Simple text cleaning
    translator = str.maketrans('', '', string.punctuation)
    resume_words = set(resume_text.lower().translate(translator).split())
    jd_words = set(jd_text.lower().translate(translator).split())
    
    # Remove common stopwords to improve signal quality
    stopwords = set(["and", "the", "is", "in", "a", "to", "of", "for", "with", "on", "as", "or", "at", "an"])
    resume_words -= stopwords
    jd_words -= stopwords

    matched = jd_words & resume_words
    missing = jd_words - resume_words

    match_score = (len(matched) / len(jd_words)) * 100 if jd_words else 0.0
    
    return sorted(list(matched)), match_score, sorted(list(missing))

def generate_cover_letter(resume_file, jd_file):
    return "Dear Hiring Manager,\n\nBased on your job description and my resume, I am confident I possess the skills and experience necessary to excel in this role..."

def export_zip_bundle(resume_file, jd_file, cover_letter):
    """Creates a ZIP file containing the resume, JD, and cover letter."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if resume_file:
            zip_file.writestr(f"Optimized_{resume_file.name}", resume_file.getvalue())
        if jd_file:
            zip_file.writestr(f"JD_{jd_file.name}", jd_file.getvalue())
        zip_file.writestr("Cover_Letter.txt", cover_letter)
    return zip_buffer.getvalue()

def run_linkedin_optimizer(linkedin_input, resume_file, jd_file):
    return {"Headline Match": "High", "About Section Gaps": "Low", "Keyword Density": "Optimal"}

def generate_resume_rebuild(resume_file, jd_file):
    return ["Optimized bullet point suggesting quantifiable achievements.", "Rephrased skill section to match job description keywords."]

def generate_scorecard(resume_file, jd_file):
    return {
        "scores": {"Skills Match": 85, "Experience Relevance": 75, "Education Alignment": 90},
        "total_score": 83,
        "interpretation": "Strong alignment with the job description. Candidate shows significant potential."
    }

# --- SIDEBAR UI ---

with st.sidebar:
    # st.image("psa_logo.png", width=150) # Assuming you have a logo
    st.title("PSA™ Optimizer")
    st.markdown("---")

    st.header("🔐 Access Control")
    license_key = st.text_input("Enter your PSA™ Pro License Key", type="password", help="Enter your license key to unlock Pro features.")
    current_license_tier = get_user_mode(license_key)

    if current_license_tier in ["pro", "enterprise"]:
        st.success("Pro License Verified!")
        st.markdown("---")
        st.header("📂 Upload Documents")
        st.session_state.resume_file = st.file_uploader("Upload your Resume", type=["pdf", "docx"])
        st.session_state.jd_file = st.file_uploader("Upload the Job Description", type=["pdf", "txt"])

        st.markdown("---")
        if st.button("🚀 Analyze Now", use_container_width=True, type="primary"):
            if st.session_state.resume_file and st.session_state.jd_file:
                with st.spinner("Analyzing signals... Please wait."):
                    # Run all analyses and store results in session state
                    matched, score, gaps = generate_signal_table(st.session_state.resume_file, st.session_state.jd_file)
                    st.session_state.analysis_results = {
                        "matched_keywords": matched,
                        "match_score": score,
                        "missing_keywords": gaps,
                        "scorecard": generate_scorecard(st.session_state.resume_file, st.session_state.jd_file),
                        "resume_rebuild": generate_resume_rebuild(st.session_state.resume_file, st.session_state.jd_file),
                        "cover_letter": generate_cover_letter(st.session_state.resume_file, st.session_state.jd_file)
                    }
                st.success("Analysis Complete!")
            else:
                st.warning("Please upload both a resume and a job description.")
    else:
        if license_key:
            st.error("Invalid License Key. Please try again.")
        st.info("Enter a valid license key to begin.")
    
    st.markdown("---")
    st.caption("© PSA™ & AIaPI™ Framework")


# --- MAIN PANEL UI ---

st.title("📄 PSA™ Resume & Career Optimizer")
st.caption("Part of the Presence Signaling Architecture (PSA™) and AI as Presence Interface (AIaPI™) framework.")

if 'analysis_results' not in st.session_state:
    st.info("Welcome! Please enter your license key and upload your documents in the sidebar to begin the analysis.")
    st.markdown("### 🔒 Privacy First\n"
              "This app respects your privacy. Your files are processed in-memory and are never stored or collected. "
              "Your session is cleared when you close this browser tab.")
else:
    # --- Results Display using Tabs ---
    results = st.session_state.analysis_results
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Scorecard & Summary", 
        "🔑 Keyword Analysis", 
        "📝 Content Generation", 
        "🔗 LinkedIn Optimizer", 
        "📦 Export Bundle"
    ])

    with tab1:
        st.header("📋 Overall Match Scorecard")
        score = results['match_score']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Resume Match Score", value=f"{score:.2f}%")
            st.progress(int(score))
        with col2:
            scorecard = results['scorecard']
            st.metric(label="Weighted PSA™ Score", value=f"{scorecard['total_score']}%", help="A proprietary score based on skills, experience, and education.")

        st.subheader("Interpretation")
        st.info(scorecard["interpretation"])

        st.subheader("Detailed Breakdown")
        for k, v in scorecard['scores'].items():
            st.write(f"**{k}:**")
            st.progress(v)

    with tab2:
        st.header("Keyword Signal Analysis")
        st.subheader("✅ Matched Keywords")
        st.info(f"Found {len(results['matched_keywords'])} matching keywords between your resume and the job description.")
        # Displaying keywords as "pills"
        st.markdown(
            f"<div style='display: flex; flex-wrap: wrap; gap: 5px;'>" +
            "".join([f"<span style='background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;'>{word}</span>" for word in results['matched_keywords']]) +
            "</div>",
            unsafe_allow_html=True
        )

        st.subheader("🚨 Missing Keywords (Gaps)")
        st.warning(f"Found {len(results['missing_keywords'])} keywords from the job description that are missing from your resume. Consider adding these if relevant.")
        st.markdown(
            f"<div style='display: flex; flex-wrap: wrap; gap: 5px;'>" +
            "".join([f"<span style='background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;'>{word}</span>" for word in results['missing_keywords']]) +
            "</div>",
            unsafe_allow_html=True
        )

    with tab3:
        st.header("AI-Powered Content Generation")
        
        with st.expander("✉️ Generated Cover Letter"):
            st.text_area("Your customized cover letter:", value=results['cover_letter'], height=300, key="cover_letter_output")

        with st.expander("🧠 Optimized Resume Line Suggestions"):
            for line in results['resume_rebuild']:
                st.markdown(f"- {line}")

    with tab4:
        st.header("🔗 LinkedIn Profile Optimization (Beta)")
        linkedin_input = st.text_area("Paste your LinkedIn 'About' section here to analyze:", height=200)
        if st.button("Analyze LinkedIn Profile"):
            with st.spinner("Optimizing..."):
                linkedin_results = run_linkedin_optimizer(linkedin_input, st.session_state.resume_file, st.session_state.jd_file)
                st.subheader("LinkedIn Match Report")
                for k, v in linkedin_results.items():
                    st.markdown(f"- **{k}:** {v}")

    with tab5:
        st.header("📦 Create and Download Submission Bundle")
        st.info("This will create a single ZIP file containing your resume, the job description, and the generated cover letter for easy submission.")
        
        zip_data = export_zip_bundle(st.session_state.resume_file, st.session_state.jd_file, results['cover_letter'])
        
        st.download_button(
            label="📥 Download Submission ZIP",
            data=zip_data,
            file_name="PSA_Submission_Bundle.zip",
            mime="application/zip",
            use_container_width=True
        )
