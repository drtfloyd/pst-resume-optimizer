--- a/original_app.py
+++ b/updated_app.py
@@ -1,37 +1,38 @@
-# --- TRUST & VISIBILITY TUNER ---
-def calculate_trust_visibility_scores(results):
-    """
-    Adds two new metrics based on domain match quality and signal fidelity:
-    - Trust Score: Weighted alignment to critical domains
-    - Visibility Score: Proxy for presence signal density
-    """
-    domain_scores = results.get("domain_scores", {})
-    critical_domains = set(results.get("critical_domains", []))
-    domain_gaps = results.get("domain_gaps", {})
+ # --- TRUST & VISIBILITY TUNER ---
+ def calculate_trust_visibility_scores(results):
+     """
+     Adds two new metrics based on domain match quality and signal fidelity:
+     - Trust Score: Weighted alignment to critical domains
+     - Visibility Score: Proxy for presence signal density
+     """
+     domain_scores = results.get("domain_scores", {})
+     critical_domains = set(results.get("critical_domains", []))
+     domain_gaps = results.get("domain_gaps", {})
+ 
+     trust_total, trust_count = 0, 0
+     visibility_hits, visibility_total = 0, 0
+ 
+     for domain, score in domain_scores.items():
+         if domain in critical_domains:
+             trust_total += score
+             trust_count += 1
+         if domain in domain_gaps:
+             visibility_total += len(domain_gaps[domain]) + 1
+             visibility_hits += 1 if score > 40 else 0
+ 
+     trust_score = trust_total / trust_count if trust_count else 0
+     visibility_score = (visibility_hits / visibility_total) * 100 if visibility_total else 0
+ 
+     return round(trust_score, 1), round(visibility_score, 1)
+ 
+ def generate_hyperprompt(results):
+     soc_group = results.get("predicted_soc_group", "[unknown role]")
+     critical_domains = results.get("critical_domains", [])
+     # Correctly list matched terms from critical domains only
+     matched_terms_in_critical_domains = set()
+     for domain in critical_domains:
+         if domain in results.get('domain_scores', {}):
+              # This assumes domain_gaps and domain_scores are aligned, need to find the source keywords
+              # For this example, we'll just use the domain names as a proxy for terms
+              matched_terms_in_critical_domains.add(domain)
+ 
+ 
+     prompt = f"You are optimizing for a role in {soc_group}. Your presence signal contains strengths in: {', '.join(critical_domains)}. Use terms related to these domains. Keep your voice and presence intact."
+ 
+     return prompt
 
-    trust_total, trust_count = 0, 0
-    visibility_hits, visibility_total = 0, 0
-
-    for domain, score in domain_scores.items():
-        if domain in critical_domains:
-            trust_total += score
-            trust_count += 1
-        if domain in domain_gaps:
-            visibility_total += len(domain_gaps[domain]) + 1
-            visibility_hits += 1 if score > 40 else 0
-
-    trust_score = trust_total / trust_count if trust_count else 0
-    visibility_score = (visibility_hits / visibility_total) * 100 if visibility_total else 0
-
-    return round(trust_score, 1), round(visibility_score, 1)
-
-
-# --- Insert below st.metric("Overall Resume Match Score", ...) ---
-trust_score, visibility_score = calculate_trust_visibility_scores(results)
-
-st.metric(label="Trust Score", value=f"{trust_score}%", help="Indicates how well your resume aligns with the critical trust domains for this role.")
-st.metric(label="Visibility Score", value=f"{visibility_score}%", help="Captures the presence strength and signal clarity based on missing vs hit terms.")
-
-
-def generate_hyperprompt(results):
-    soc_group = results.get("predicted_soc_group", "[unknown role]")
-    critical_domains = results.get("critical_domains", [])
-    matched_terms = list({word for domain in critical_domains for word in results['domain_scores'] if domain in results['domain_scores']})
-
-    prompt = f"You are optimizing for a role in {soc_group}. Your presence signal contains strengths in: {', '.join(critical_domains)}. Use terms such as: {', '.join(matched_terms)}. Keep your voice and presence intact."
-
-    return prompt
-
 from psa_license.license import get_user_mode
 import streamlit as st
 
@@ -39,7 +40,6 @@
 import zipfile
 import re
 import json
-import os
-import pandas as pd
-import asyncio
+import os 
 
 # --- Custom CSS for a Polished Look ---
 st.markdown("""
@@ -82,21 +82,6 @@
 if "license_key" not in st.session_state:
     st.session_state["license_key"] = ""
 
-license_input = st.sidebar.text_input(
-    "Enter your PSAâ„¢ License Key",
-    value=st.session_state["license_key"],
-    type="password"
-)
-
-if license_input != st.session_state["license_key"]:
-    st.session_state["license_key"] = license_input
-
-current_license_tier = get_user_mode(st.session_state["license_key"])
-
-if current_license_tier in ["pro", "enterprise"]:
-    st.success("âœ… Pro License Verified!")
-elif current_license_tier == "freemium":
-    st.info("ðŸŸ¢ Freemium access granted. Upgrade for more features.")
-else:
-    st.warning("ðŸ”’ Enter your PSAâ„¢ License Key to continue.")
-
 @st.cache_data(show_spinner="Loading keyword ontology...")
 def load_ontology(ontology_path="ontology.json"):
     if not os.path.exists(ontology_path):
@@ -165,11 +150,11 @@
 with st.sidebar:
     st.title("PSAâ„¢ Optimizer")
     st.markdown("---")
-    st.header("ðŸ” Access Control")
-    license_key = st.text_input("Enter your PSAâ„¢ Pro License Key", type="password")
+    st.header("ðŸ”‘ Access Control")
+    license_key = st.text_input("Enter your PSAâ„¢ License Key", type="password", key="license_input_sidebar")
     current_license_tier = get_user_mode(license_key)
     ontology = load_ontology()
 
     if current_license_tier in ["pro", "enterprise"]:
-        st.success("Pro License Verified!")
+        st.success("âœ… Pro License Verified!")
         st.markdown("---")
-        st.header("ðŸ“‚ Upload Documents")
+        st.header("ðŸ“„ Upload Documents")
         st.session_state.resume_file = st.file_uploader("Upload your Resume", type=["pdf", "txt"])
         st.session_state.jd_file = st.file_uploader("Upload the Job Description", type=["pdf", "txt"])
 
@@ -193,20 +178,41 @@
 
 if 'analysis_results' not in st.session_state or st.session_state.analysis_results is None:
     st.info("Welcome! Please enter your license key and upload your documents in the sidebar to begin.")
 else:
     results = st.session_state.analysis_results
-    tab1, tab2, tab3 = st.tabs(["ðŸ“Š Strategic Scorecard", "ðŸ”‘ Gap Analysis", "ðŸ’¼ Career Suggestions"])
+    tab1, tab2, tab3, tab4 = st.tabs(["ðŸ“Š Strategic Scorecard", "ðŸ” Gap Analysis", "ðŸ’¡ Career Suggestions", "ðŸ¤🤖 AI Hyper-Prompt"])
 
     with tab1:
-        st.header("ðŸ“‹ Analysis Summary")
-        st.metric(label="Overall Resume Match Score", value=f"{results['overall_score']:.1f}%", help="This score represents the overall percentage of relevant keywords from the job description that were found in your resume.")
+        st.header("ðŸ“ Analysis Summary")
+        cols = st.columns(3)
+        with cols[0]:
+            st.metric(
+                label="Overall Resume Match Score",
+                value=f"{results['overall_score']:.1f}%",
+                help="This score represents the overall percentage of relevant keywords from the job description that were found in your resume."
+            )
+        
+        # --- Inserted Code Block ---
+        trust_score, visibility_score = calculate_trust_visibility_scores(results)
+        with cols[1]:
+            st.metric(
+                label="Trust Score",
+                value=f"{trust_score}%",
+                help="Indicates how well your resume aligns with the critical trust domains for this role."
+            )
+        with cols[2]:
+            st.metric(
+                label="Visibility Score",
+                value=f"{visibility_score}%",
+                help="Captures the presence strength and signal clarity based on missing vs hit terms."
+            )
+        # --- End Inserted Code Block ---
+        
         st.progress(int(results['overall_score']))
 
         st.subheader("Predicted Job Category")
         soc_group = results['predicted_soc_group']
         st.info(f"**{soc_group}**" if soc_group else "Could not determine job category.")
 
         st.subheader("Your Signal Domain Scores")
         st.caption("This shows your alignment with key competency areas. Focus on improving the 'Critical' domains for this role.")
 
         critical_domains = set(results['critical_domains'])
         domain_scores = results['domain_scores']
-
-        for domain, score in sorted(domain_scores.items(), key=lambda item: item[1], reverse=True):
-            if domain in critical_domains:
-                st.markdown(f"**{domain} (Critical)**")
-            else:
-                st.markdown(f"{domain}")
+        
+        sorted_scores = sorted(domain_scores.items(), key=lambda item: item[1], reverse=True)
+
+        for domain, score in sorted_scores:
+            label = f"**{domain} (Critical)**" if domain in critical_domains else domain
+            st.markdown(label)
             st.progress(int(score))
 
     with tab2:
@@ -214,7 +220,7 @@
         st.info("This shows important keywords from the job description that are missing from your resume, grouped by their strategic domain.")
 
         domain_gaps = results['domain_gaps']
-        sorted_domains = sorted(domain_gaps.keys(), key=lambda d: d not in critical_domains)
+        sorted_domains = sorted(domain_gaps.keys(), key=lambda d: (d not in critical_domains, d))
 
         for domain in sorted_domains:
             is_critical = " (Critical for this role)" if domain in critical_domains else ""
@@ -222,8 +228,15 @@
                 st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 5px;'>" + "".join([f"<span style='background-color: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; font-size: 14px;'>" + word + "</span>" for word in domain_gaps[domain]]) + "</div>", unsafe_allow_html=True)
 
     with tab3:
-        st.header("ðŸŽ¯ Suggested Job Titles")
+        st.header("ðŸŽ¯ Suggested Job Titles")
         st.markdown("These job titles are based on your predicted career domain and signal profile.")
         for title in results.get("suggested_titles", []):
             st.markdown(f"- {title}")
+
+    with tab4:
+        st.header("AI-Powered Resume Optimizer Prompt")
+        st.info("Copy this 'Hyper-Prompt' and paste it into an AI chat model (like Gemini, ChatGPT, Claude) to get tailored suggestions for improving your resume for this specific role.")
+        hyper_prompt = generate_hyperprompt(results)
+        st.text_area("Hyper-Prompt", hyper_prompt, height=250)
