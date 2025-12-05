# streamlit_app.py
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Medical Prescription Firewall", layout="wide")

ROOT = os.path.dirname(__file__) or "."

# Load data files (adjust paths if you placed them in data/)
PRESCRIBERS_XLSX = os.path.join(ROOT, "medical_prescribers_50.xlsx")
PATIENTS_XLSX = os.path.join(ROOT, "medical_patients_100.xlsx")
HTML_DEMO = os.path.join(ROOT, "firewall.html")

@st.cache_data(ttl=3600)
def load_prescribers(path=PRESCRIBERS_XLSX):
    if os.path.exists(path):
        return pd.read_excel(path)
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_patients(path=PATIENTS_XLSX):
    if os.path.exists(path):
        return pd.read_excel(path)
    return pd.DataFrame()

prescribers_df = load_prescribers()
patients_df = load_patients()

st.title("Medical Prescription Firewall — Streamlit Demo")

col1, col2 = st.columns([2,1])

with col1:
    st.markdown("### Live Demo (embedded `firewall.html`)")
    if os.path.exists(HTML_DEMO):
        try:
            # Embed raw HTML demo
            with open(HTML_DEMO, "r", encoding="utf-8") as f:
                html = f.read()
            st.components.v1.html(html, height=700, scrolling=True)
        except Exception as e:
            st.error(f"Couldn't embed firewall.html: {e}")
            st.info("You can still use the interactive tester below.")
    else:
        st.info("No `firewall.html` found in repo root.")

with col2:
    st.markdown("### Interactive Tester")
    # prescriber selector
    if not prescribers_df.empty:
        prescriber_cols = list(prescribers_df.columns)
        display_pres = prescribers_df.copy()
        # Try to identify id and name columns
        id_col = None
        name_col = None
        for c in prescriber_cols:
            if c.lower().startswith("id") or "doc" in c.lower() or "code" in c.lower():
                id_col = c
            if c.lower().startswith("name") or "doctor" in c.lower():
                name_col = c
        if id_col is None:
            id_col = prescriber_cols[0]
        if name_col is None and len(prescriber_cols) > 1:
            name_col = prescriber_cols[1]
        display_pres["__label__"] = display_pres[id_col].astype(str) + " — " + display_pres[name_col].astype(str) if name_col in display_pres else display_pres[id_col].astype(str)
        presc_choice = st.selectbox("Prescriber", ["Select"] + display_pres["__label__"].tolist())
    else:
        st.info("No prescriber data loaded. Upload `medical_prescribers_50.xlsx` to repo root.")
        presc_choice = st.text_input("Prescriber ID", value="DOC001")

    # patient selector
    if not patients_df.empty:
        patient_cols = list(patients_df.columns)
        pid_col = None
        pname_col = None
        for c in patient_cols:
            if c.lower().startswith("id") or "p" in c.lower() and "id" in c.lower():
                pid_col = c
            if c.lower().startswith("name"):
                pname_col = c
        if pid_col is None:
            pid_col = patient_cols[0]
        display_pat = patients_df.copy()
        if pname_col:
            display_pat["__label__"] = display_pat[pid_col].astype(str) + " — " + display_pat[pname_col].astype(str)
        else:
            display_pat["__label__"] = display_pat[pid_col].astype(str)
        pat_choice = st.selectbox("Patient", ["Select"] + display_pat["__label__"].tolist())
    else:
        st.info("No patient data loaded. Upload `medical_patients_100.xlsx` to repo root.")
        pat_choice = st.text_input("Patient ID", value="P001")

    st.text_input("Drug name", key="drug", value="Oxycodone")
    st.text_input("Dose (e.g. 10mg)", key="dose", value="10mg")

    analyze_btn = st.button("Analyze Prescription")

    # Try to import your engine if available
    analyze_func = None
    try:
        from firewall_engine import analyze_prescription
        analyze_func = analyze_prescription
    except Exception:
        analyze_func = None

    if analyze_btn:
        presc_id = presc_choice if isinstance(presc_choice, str) else "DOC001"
        pat_id = pat_choice if isinstance(pat_choice, str) else "P001"
        drug = st.session_state.get("drug", "Oxycodone")
        dose = st.session_state.get("dose", "10mg")

        # If we have engine, use it
        if analyze_func:
            try:
                result = analyze_func(presc_id, pat_id, drug, dose)
                st.success("Result from firewall_engine.py")
                st.json(result)
            except Exception as e:
                st.error(f"Error calling analyze_prescription: {e}")
        else:
            # Fallback simple checks: existence in sheets + simple rules
            reasons = []
            approved = True
            # prescriber check
            if not prescribers_df.empty:
                if presc_choice == "Select":
                    reasons.append("No prescriber selected")
                    approved = False
                else:
                    reasons.append("Prescriber found")
            # patient check
            if not patients_df.empty:
                if pat_choice == "Select":
                    reasons.append("No patient selected")
                    approved = False
                else:
                    reasons.append("Patient found")

                # Example: Check liver/kidney status columns if present
                for organ_col in ["liver_status", "kidney_status", "organ_status"]:
                    if organ_col in (c.lower() for c in patients_df.columns):
                        # demo only: block if 'poor' or 'dysfunction'
                        v = patients_df.iloc[0].get(organ_col, "")
                        if isinstance(v, str) and ("poor" in v.lower() or "dysfunction" in v.lower()):
                            reasons.append(f"Patient organ concern: {organ_col}={v}")
                            approved = False

            # drug checks - very simple demo rules
            dname = drug.lower()
            dose_num = None
            try:
                dose_num = float("".join(ch for ch in dose if (ch.isdigit() or ch=='.')))
            except:
                dose_num = None

            if "heroin" in dname or "illegal" in dname:
                reasons.append("Illegal/controlled drug")
                approved = False
            if dose_num and dose_num > 50:
                reasons.append("Dose exceeds typical safety threshold (demo rule)")
                approved = False

            st.write("### Firewall Decision")
            if approved:
                st.success("✅ APPROVED")
            else:
                st.error("⛔ BLOCKED")

            st.write("### Reasons")
            for r in reasons:
                st.write("- " + r)

st.sidebar.markdown("### Repo / Deploy")
st.sidebar.markdown("Files loaded:")
st.sidebar.write(f"- Prescribers: {'Yes' if not prescribers_df.empty else 'No'}")
st.sidebar.write(f"- Patients: {'Yes' if not patients_df.empty else 'No'}")
st.sidebar.write(f"- firewall.html: {'Yes' if os.path.exists(HTML_DEMO) else 'No'}")
st.sidebar.markdown("---")
st.sidebar.info("To deploy on Streamlit Cloud, push this repo to GitHub and connect from streamlit.io/sharing")
