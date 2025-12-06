"""
Medical Prescription Firewall - Streamlit Dashboard
Interactive tester for 4-layer prescription safety analysis
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Try to import firewall_engine
try:
    from firewall_engine import PrescriptionFirewall
    firewall = PrescriptionFirewall()
    has_firewall = True
except:
    firewall = None
    has_firewall = False

# Page config
st.set_page_config(
    page_title="Medical Prescription Firewall",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .approved { color: #28a745; font-weight: bold; }
    .blocked { color: #dc3545; font-weight: bold; }
    .warning { color: #ffc107; font-weight: bold; }
    .info { color: #17a2b8; font-weight: bold; }
    .layer-passed { border-left: 4px solid #28a745; padding: 10px; margin: 5px 0; background-color: #f0f8f5; }
    .layer-failed { border-left: 4px solid #dc3545; padding: 10px; margin: 5px 0; background-color: #f8f0f0; }
    .metric-box { padding: 15px; border-radius: 5px; background-color: #f5f5f5; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ============== LOAD DATA ==============

@st.cache_data
def load_data():
    """Load prescriber and patient data from Excel files"""
    try:
        prescribers = pd.read_excel('medical_prescribers_50.xlsx')
        patients = pd.read_excel('medical_patients_100.xlsx')
        return prescribers, patients
    except:
        return None, None

prescribers_df, patients_df = load_data()

# ============== HELPER FUNCTIONS ==============

def extract_id_from_label(label_string, dataframe, id_col):
    """
    Extract the actual ID from a display label.
    Label format: "DOC001 — Dr. Smith" or "P001 — Sarah Davis"
    We need just the ID part (before the " — " separator)
    """
    if label_string == "Select":
        return None
    
    if not label_string:
        return None
    
    # Split on the separator (—, -, |, or whitespace)
    for sep in ["—", "-", "|", " "]:
        if sep in str(label_string):
            id_part = str(label_string).split(sep)[0].strip()
            if id_part and id_part != "":
                return id_part
    
    return str(label_string).strip()


def get_selected_patient_row(patient_id, patients_df, id_col="patient_id"):
    """
    Get the ACTUAL selected patient row from dataframe.
    NOT iloc[0] — use the patient_id to find the correct row.
    """
    if patients_df is None or patients_df.empty:
        return None
    
    if patient_id is None:
        return None
    
    # Find the row matching the patient_id
    matching_rows = patients_df[patients_df[id_col].astype(str) == str(patient_id)]
    
    if matching_rows.empty:
        return None
    
    return matching_rows.iloc[0]  # Now safe to use iloc[0] since we filtered


def get_selected_prescriber_row(prescriber_id, prescribers_df, id_col="doctor_id"):
    """
    Get the ACTUAL selected prescriber row from dataframe.
    """
    if prescribers_df is None or prescribers_df.empty:
        return None
    
    if prescriber_id is None:
        return None
    
    matching_rows = prescribers_df[prescribers_df[id_col].astype(str) == str(prescriber_id)]
    
    if matching_rows.empty:
        return None
    
    return matching_rows.iloc[0]


def parse_dose(dose_str):
    """Parse dose string and extract numeric value"""
    try:
        # Extract all digits and decimal point
        dose_num = ''.join(c for c in str(dose_str) if c.isdigit() or c == '.')
        if dose_num:
            return float(dose_num)
        return 10.0
    except:
        return 10.0


def get_safe_dose_limit(drug):
    """Get safe dose limit for a drug"""
    limits = {
        'oxycodone': 50,
        'morphine': 100,
        'hydrocodone': 40,
        'codeine': 60,
        'paracetamol': 1000,
        'ibuprofen': 800,
        'aspirin': 500,
        'metformin': 2550,
        'lisinopril': 40,
        'atenolol': 100,
        'vitamin_d': 4000,
        'atorvastatin': 80,
        'amlodipine': 10,
        'albuterol': 200,
        'insulin': 300
    }
    return limits.get(drug.lower(), None)


def check_contraindications(selected_patient, drug, patients_df):
    """Check for drug-disease and organ contraindications"""
    if selected_patient is None:
        return True, "No patient data"
    
    contraindications = []
    
    # Get organ status columns
    liver_status = None
    kidney_status = None
    
    for col in patients_df.columns:
        if "liver" in col.lower():
            liver_status = str(selected_patient.get(col, "")).lower()
        if "kidney" in col.lower():
            kidney_status = str(selected_patient.get(col, "")).lower()
    
    drug_lower = drug.lower().strip()
    
    # OPIOID CONTRAINDICATIONS
    if drug_lower in ['oxycodone', 'morphine', 'hydrocodone', 'codeine']:
        if liver_status and ("severe" in liver_status or "impaired" in liver_status):
            contraindications.append(f"⚠️ {drug} contraindicated with {liver_status} liver disease")
        
        if kidney_status and "severe" in kidney_status:
            contraindications.append(f"⚠️ {drug} contraindicated with severe kidney disease")
    
    # NSAID CONTRAINDICATIONS
    if drug_lower in ['aspirin', 'ibuprofen']:
        if kidney_status and ("impaired" in kidney_status or "disease" in kidney_status):
            contraindications.append(f"⚠️ NSAIDs contraindicated with kidney disease")
    
    # METFORMIN CONTRAINDICATIONS
    if drug_lower == 'metformin':
        if kidney_status and ("impaired" in kidney_status or "severe" in kidney_status):
            contraindications.append(f"⚠️ Metformin contraindicated with kidney impairment")
    
    if contraindications:
        return False, " | ".join(contraindications)
    
    return True, "No contraindications detected"


# ============== SIDEBAR ==============

with st.sidebar:
    st.title("🏥 Medical Prescription Firewall")
    st.markdown("### 4-Layer Clinical Decision Support System")
    st.divider()
    
    st.markdown("**System Status:**")
    col1, col2 = st.columns(2)
    
    if prescribers_df is not None and patients_df is not None:
        with col1:
            st.metric("Doctors", len(prescribers_df))
        with col2:
            st.metric("Patients", len(patients_df))
        st.success("✅ Data loaded")
    else:
        st.error("❌ Data not loaded")
    
    if has_firewall:
        st.info("✅ Firewall engine: Available")
    else:
        st.warning("⚠️ Using fallback logic")
    
    st.divider()
    st.markdown("**About**")
    st.markdown("""
    This system analyzes prescriptions through 4 safety layers:
    - **Layer 0:** Doctor authorization
    - **Layer 1:** Patient validation  
    - **Layer 2:** Drug safety
    - **Layer 3:** Contraindication detection
    """)

# ============== MAIN CONTENT ==============

st.title("🛡️ Medical Prescription Firewall v3.0")
st.markdown("**Real-time prescription safety analysis with 4-layer verification**")

# Create tabs
tab1, tab2, tab3 = st.tabs(["🧪 Interactive Tester", "📊 Analysis History", "ℹ️ About"])

with tab1:
    st.subheader("Prescription Analysis")
    
    if prescribers_df is None or patients_df is None:
        st.error("❌ Unable to load data files. Please ensure medical_prescribers_50.xlsx and medical_patients_100.xlsx are available.")
    else:
        # Create display versions with labels
        prescribers_df['__label__'] = prescribers_df.apply(
            lambda row: f"{row['doctor_id']} — {row['name']}", axis=1
        )
        patients_df['__label__'] = patients_df.apply(
            lambda row: f"{row['patient_id']} — {row['name']}", axis=1
        )
        
        # Input columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            presc_choice = st.selectbox(
                "Select Doctor",
                ["Select"] + prescribers_df['__label__'].tolist(),
                key="prescriber"
            )
        
        with col2:
            pat_choice = st.selectbox(
                "Select Patient",
                ["Select"] + patients_df['__label__'].tolist(),
                key="patient"
            )
        
        with col3:
            drug_input = st.text_input(
                "Drug Name",
                value="Oxycodone",
                key="drug"
            )
        
        with col4:
            dose_input = st.text_input(
                "Dose (mg)",
                value="10",
                key="dose"
            )
        
        st.divider()
        
        # Analyze button
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            analyze_btn = st.button("🔍 Analyze Prescription", use_container_width=True)
        
        if analyze_btn:
            # Extract actual IDs from labels
            presc_id = extract_id_from_label(presc_choice, prescribers_df, "doctor_id")
            pat_id = extract_id_from_label(pat_choice, patients_df, "patient_id")
            
            drug = drug_input.strip() if drug_input else "Oxycodone"
            dose = parse_dose(dose_input)
            
            if presc_id is None or pat_id is None:
                st.error("❌ Please select both a doctor and patient")
            else:
                # ===== GET SELECTED ROWS (NOT iloc[0]) =====
                selected_patient = get_selected_patient_row(pat_id, patients_df, "patient_id")
                selected_prescriber = get_selected_prescriber_row(presc_id, prescribers_df, "doctor_id")
                
                with st.spinner("Analyzing prescription..."):
                    # Run analysis
                    if has_firewall and firewall is not None:
                        # Use the real firewall_engine
                        try:
                            result = firewall.analyze_prescription(
                                prescriber_id=presc_id,
                                patient_id=pat_id,
                                drug=drug,
                                dose=dose
                            )
                        except Exception as e:
                            st.error(f"Error in firewall engine: {str(e)}")
                            result = None
                    else:
                        # Fallback: Build result using selected rows
                        result = {
                            "approved": True,
                            "prescriber_id": presc_id,
                            "patient_id": pat_id,
                            "drug": drug,
                            "dose": dose,
                            "layer0": {"passed": True, "message": "✅ Prescriber authorized"},
                            "layer1": {"passed": True, "message": "✅ Patient found"},
                            "layer2": {"passed": True, "message": "✅ Drug valid"},
                            "layer3": {"passed": True, "message": "✅ No contraindications"},
                            "safety_score": 100,
                            "reason": "✅ APPROVED - All checks passed",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Layer 0: Check prescriber
                        if selected_prescriber is not None:
                            status = selected_prescriber.get('credentialing_status', 'Unknown')
                            if status != 'Active':
                                result["approved"] = False
                                result["layer0"]["passed"] = False
                                result["layer0"]["message"] = f"❌ Prescriber status: {status}"
                                result["safety_score"] = 0
                        
                        # Layer 1: Check patient
                        if selected_patient is None:
                            result["approved"] = False
                            result["layer1"]["passed"] = False
                            result["layer1"]["message"] = "❌ Patient not found"
                            result["safety_score"] = 0
                        
                        # Layer 2: Check drug safety
                        safe_limit = get_safe_dose_limit(drug)
                        if safe_limit and dose > safe_limit:
                            result["approved"] = False
                            result["layer2"]["passed"] = False
                            result["layer2"]["message"] = f"❌ Dose {dose}mg exceeds safe limit of {safe_limit}mg"
                            result["safety_score"] = 25
                        
                        # Layer 3: Check contraindications (using selected_patient)
                        if result["approved"] and selected_patient is not None:
                            safe, contra_msg = check_contraindications(selected_patient, drug, patients_df)
                            if not safe:
                                result["approved"] = False
                                result["layer3"]["passed"] = False
                                result["layer3"]["message"] = contra_msg
                                result["safety_score"] = 25
                    
                    if result:
                        st.divider()
                        
                        # Decision Box
                        if result["approved"]:
                            st.success(f"### ✅ APPROVED", icon="✅")
                            st.markdown(f"**Safety Score:** {result['safety_score']}/100")
                        else:
                            st.error(f"### 🚫 BLOCKED", icon="❌")
                            st.markdown(f"**Reason:** {result['reason']}")
                            st.markdown(f"**Safety Score:** {result['safety_score']}/100")
                        
                        st.divider()
                        
                        # Layer Details
                        st.subheader("Layer Analysis")
                        
                        # Layer 0
                        if result["layer0"]["passed"]:
                            st.markdown(f'<div class="layer-passed">✅ <b>Layer 0 - Doctor Authorization:</b> {result["layer0"]["message"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="layer-failed">❌ <b>Layer 0 - Doctor Authorization:</b> {result["layer0"]["message"]}</div>', unsafe_allow_html=True)
                        
                        # Layer 1
                        if result["layer1"]["passed"]:
                            st.markdown(f'<div class="layer-passed">✅ <b>Layer 1 - Patient Validation:</b> {result["layer1"]["message"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="layer-failed">❌ <b>Layer 1 - Patient Validation:</b> {result["layer1"]["message"]}</div>', unsafe_allow_html=True)
                        
                        # Layer 2
                        if result["layer2"]["passed"]:
                            st.markdown(f'<div class="layer-passed">✅ <b>Layer 2 - Drug Safety:</b> {result["layer2"]["message"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="layer-failed">❌ <b>Layer 2 - Drug Safety:</b> {result["layer2"]["message"]}</div>', unsafe_allow_html=True)
                        
                        # Layer 3
                        if result["layer3"]["passed"]:
                            st.markdown(f'<div class="layer-passed">✅ <b>Layer 3 - Contraindication Detection:</b> {result["layer3"]["message"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="layer-failed">❌ <b>Layer 3 - Contraindication Detection:</b> {result["layer3"]["message"]}</div>', unsafe_allow_html=True)
                        
                        st.divider()
                        
                        # Details
                        st.subheader("Prescription Details")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Doctor ID", presc_id)
                        with col2:
                            st.metric("Patient ID", pat_id)
                        with col3:
                            st.metric("Drug", drug)
                        with col4:
                            st.metric("Dose", f"{dose} mg")
                        
                        # Show patient details if available
                        if selected_patient is not None:
                            st.subheader("Patient Medical History")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Age:** {selected_patient.get('age', 'N/A')}")
                                conditions = selected_patient.get('conditions', '')
                                if conditions:
                                    st.markdown(f"**Conditions:** {conditions}")
                            
                            with col2:
                                medications = selected_patient.get('medications', '')
                                if medications:
                                    st.markdown(f"**Current Medications:** {medications}")
                                
                                liver = selected_patient.get('liver_status', 'normal')
                                kidney = selected_patient.get('kidney_status', 'normal')
                                st.markdown(f"**Organ Status:** Liver: {liver} | Kidney: {kidney}")

with tab2:
    st.subheader("📊 Analysis History")
    st.info("Analysis history tracking coming soon!")
    st.markdown("""
    Future features:
    - View previous analyses
    - Export reports
    - Trend analysis
    - Patient timeline
    """)

with tab3:
    st.subheader("ℹ️ System Information")
    
    st.markdown("""
    ### How It Works
    
    **4-Layer Prescription Firewall:**
    
    **Layer 0: Doctor Authorization**
    - Verifies doctor exists in database
    - Checks DEA number is valid
    - Confirms license is active (not suspended/revoked)
    - Validates prescribing privileges
    
    **Layer 1: Patient Validation**
    - Confirms patient exists
    - Loads medical history
    - Retrieves current medications
    - Checks organ function status
    
    **Layer 2: Drug Safety**
    - Validates drug is legal/approved
    - Checks dosage is within safe limits
    - Blocks dangerous drug combinations
    - Verifies proper strength/formulation
    
    **Layer 3: Contraindication Detection**
    - Checks drug-disease interactions
    - Detects drug-drug conflicts
    - Considers organ function
    - High-risk combination warnings
    
    ### Data Sources
    
    - **Prescribers:** 50 doctors from medical_prescribers_50.xlsx
    - **Patients:** 100 patients from medical_patients_100.xlsx
    - **Safety Rules:** Evidence-based medical guidelines
    
    ### Safety Scoring
    
    - **100/100:** All layers pass - safe to prescribe
    - **75/100:** Minor warnings - prescriber review recommended
    - **50/100:** Significant concerns - contraindication detected
    - **0-25/100:** Critical issue - prescription blocked
    """)

st.divider()
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>🏥 Medical Prescription Firewall v3.0</p>
    <p>4-Layer Clinical Decision Support System | Powered by Streamlit</p>
    <p><small>For demonstration purposes. Always consult qualified healthcare professionals.</small></p>
</div>
""", unsafe_allow_html=True)
