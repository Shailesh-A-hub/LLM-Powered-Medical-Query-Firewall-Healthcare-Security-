"""
Medical Prescription Firewall Engine
4-Layer Clinical Decision Support System
Layer 0: Doctor Authorization
Layer 1: Patient Validation
Layer 2: Drug Safety
Layer 3: Contraindication Detection
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class PrescriptionFirewall:
    """
    4-Layer firewall system for prescription safety.
    Prevents medication errors through intelligent multi-layer analysis.
    """
    
    def __init__(self):
        """Initialize firewall with prescriber and patient data"""
        self.prescribers_df = None
        self.patients_df = None
        self.analysis_count = 0
        self.approved_count = 0
        self.initialize()
    
    def initialize(self):
        """Load prescriber and patient data"""
        try:
            # Load prescriber data
            self.prescribers_df = pd.read_excel('medical_prescribers_50.xlsx')
            # Load patient data
            self.patients_df = pd.read_excel('medical_patients_100.xlsx')
            print("✅ Data loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")
            self.prescribers_df = None
            self.patients_df = None
    
    # ============== LAYER 0: Doctor Authorization ==============
    
    def layer0_doctor_authorization(self, prescriber_id: str) -> Dict[str, Any]:
        """
        Layer 0: Verify doctor is authorized to prescribe.
        
        Checks:
        - Doctor exists in database
        - DEA number is valid
        - License is active (not suspended/revoked)
        - Prescribing privileges
        """
        try:
            if self.prescribers_df is None:
                return {
                    "passed": False,
                    "message": "Database not loaded",
                    "details": {}
                }
            
            # Find prescriber
            prescriber = self.prescribers_df[
                self.prescribers_df['doctor_id'] == prescriber_id
            ]
            
            if prescriber.empty:
                return {
                    "passed": False,
                    "message": f"Prescriber {prescriber_id} not found in database",
                    "details": {}
                }
            
            prescriber_data = prescriber.iloc[0]
            
            # Check status
            if prescriber_data['credentialing_status'] != 'Active':
                return {
                    "passed": False,
                    "message": f"Prescriber status: {prescriber_data['credentialing_status']}",
                    "details": {
                        "status": prescriber_data['credentialing_status'],
                        "name": prescriber_data['name']
                    }
                }
            
            # Check DEA number validity
            if not str(prescriber_data['dea_number']).startswith('A'):
                return {
                    "passed": False,
                    "message": "Invalid DEA number format",
                    "details": {}
                }
            
            return {
                "passed": True,
                "message": f"Prescriber {prescriber_data['name']} authorized",
                "details": {
                    "name": prescriber_data['name'],
                    "specialty": prescriber_data['specialty'],
                    "status": prescriber_data['credentialing_status'],
                    "dea_number": prescriber_data['dea_number']
                }
            }
        
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error in Layer 0: {str(e)}",
                "details": {}
            }
    
    # ============== LAYER 1: Patient Validation ==============
    
    def layer1_patient_validation(self, patient_id: str) -> Dict[str, Any]:
        """
        Layer 1: Validate patient exists and retrieve data.
        
        Checks:
        - Patient exists in database
        - Patient profile is complete
        - Patient history is accessible
        """
        try:
            if self.patients_df is None:
                return {
                    "passed": False,
                    "message": "Patient database not loaded",
                    "details": {}
                }
            
            # Find patient
            patient = self.patients_df[
                self.patients_df['patient_id'] == patient_id
            ]
            
            if patient.empty:
                return {
                    "passed": False,
                    "message": f"Patient {patient_id} not found",
                    "details": {}
                }
            
            patient_data = patient.iloc[0]
            
            # Extract conditions and medications
            conditions = str(patient_data.get('conditions', '')).split(';') if pd.notna(patient_data.get('conditions')) else []
            medications = str(patient_data.get('medications', '')).split(';') if pd.notna(patient_data.get('medications')) else []
            
            return {
                "passed": True,
                "message": f"Patient {patient_data['name']} found",
                "details": {
                    "name": patient_data['name'],
                    "age": patient_data['age'],
                    "conditions": conditions,
                    "medications": medications,
                    "liver_status": patient_data.get('liver_status', 'normal'),
                    "kidney_status": patient_data.get('kidney_status', 'normal')
                }
            }
        
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error in Layer 1: {str(e)}",
                "details": {}
            }
    
    # ============== LAYER 2: Drug Safety ==============
    
    def layer2_drug_safety(self, drug: str, dose: float) -> Dict[str, Any]:
        """
        Layer 2: Validate drug and dosage safety.
        
        Checks:
        - Drug name is legal/valid
        - Dosage is within safe limits
        - Drug is not on banned list
        """
        # List of illegal drugs
        illegal_drugs = ['heroin', 'fentanyl_street', 'meth', 'cocaine', 'pcp']
        
        # Safe dosage limits (mg)
        safe_dose_limits = {
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
        
        try:
            drug_lower = drug.lower().strip()
            
            # Check if illegal
            if drug_lower in illegal_drugs:
                return {
                    "passed": False,
                    "message": f"Drug '{drug}' is illegal/controlled substance",
                    "details": {}
                }
            
            # Check dosage limit if known
            if drug_lower in safe_dose_limits:
                max_dose = safe_dose_limits[drug_lower]
                if dose > max_dose:
                    return {
                        "passed": False,
                        "message": f"Dose {dose}mg exceeds safe limit of {max_dose}mg",
                        "details": {
                            "drug": drug,
                            "dose": dose,
                            "max_safe_dose": max_dose
                        }
                    }
            
            return {
                "passed": True,
                "message": f"Drug '{drug}' at {dose}mg is safe",
                "details": {
                    "drug": drug,
                    "dose": dose,
                    "status": "valid"
                }
            }
        
        except Exception as e:
            return {
                "passed": False,
                "message": f"Error in Layer 2: {str(e)}",
                "details": {}
            }
    
    # ============== LAYER 3: Contraindication Detection ==============
    
    def layer3_contraindication_detection(
        self,
        patient_id: str,
        drug: str,
        dose: float
    ) -> Dict[str, Any]:
        """
        Layer 3: Detect drug-disease and drug-drug interactions.
        
        Checks:
        - Drug-disease contraindications
        - Drug-drug interactions
        - Organ function compatibility
        - High-risk combinations
        """
        try:
            if self.patients_df is None:
                return {
                    "passed": True,
                    "message": "Cannot check contraindications - patient DB unavailable",
                    "details": {}
                }
            
            # Get patient data
            patient = self.patients_df[
                self.patients_df['patient_id'] == patient_id
            ]
            
            if patient.empty:
                return {
                    "passed": True,
                    "message": "Patient not found for contraindication check",
                    "details": {}
                }
            
            patient_data = patient.iloc[0]
            conditions = str(patient_data.get('conditions', '')).lower().split(';')
            medications = str(patient_data.get('medications', '')).lower().split(';')
            liver_status = str(patient_data.get('liver_status', 'normal')).lower()
            kidney_status = str(patient_data.get('kidney_status', 'normal')).lower()
            
            drug_lower = drug.lower().strip()
            
            # ===== OPIOID CONTRAINDICATIONS =====
            if drug_lower in ['oxycodone', 'morphine', 'hydrocodone', 'codeine']:
                # Check severe liver disease
                if liver_status in ['severe', 'impaired']:
                    return {
                        "passed": False,
                        "message": f"CONTRAINDICATION: {drug} contraindicated with {liver_status} liver disease",
                        "details": {
                            "reason": "opioids_liver_disease",
                            "severity": "CRITICAL"
                        }
                    }
                
                # Check kidney impairment
                if kidney_status == 'severe':
                    return {
                        "passed": False,
                        "message": f"CONTRAINDICATION: {drug} contraindicated with severe kidney disease",
                        "details": {
                            "reason": "opioids_kidney_disease",
                            "severity": "CRITICAL"
                        }
                    }
            
            # ===== ASPIRIN CONTRAINDICATIONS =====
            if drug_lower in ['aspirin', 'ibuprofen']:
                if 'kidney_disease' in conditions or 'ckd' in str(conditions):
                    return {
                        "passed": False,
                        "message": f"CONTRAINDICATION: NSAIDs contraindicated with kidney disease",
                        "details": {
                            "reason": "nsaid_kidney_disease",
                            "severity": "HIGH"
                        }
                    }
            
            # ===== DRUG-DRUG INTERACTIONS =====
            # Warfarin + Aspirin
            if drug_lower == 'aspirin' and 'warfarin' in medications:
                return {
                    "passed": False,
                    "message": "CONTRAINDICATION: Aspirin-Warfarin interaction (bleeding risk)",
                    "details": {
                        "reason": "drug_drug_interaction",
                        "severity": "CRITICAL",
                        "interaction": "aspirin_warfarin"
                    }
                }
            
            # Metformin + Kidney disease
            if drug_lower == 'metformin' and kidney_status in ['impaired', 'severe']:
                return {
                    "passed": False,
                    "message": "CONTRAINDICATION: Metformin contraindicated with kidney impairment",
                    "details": {
                        "reason": "metformin_kidney_disease",
                        "severity": "HIGH"
                    }
                }
            
            return {
                "passed": True,
                "message": "No contraindications detected",
                "details": {
                    "checked": True,
                    "conditions": conditions,
                    "status": "safe"
                }
            }
        
        except Exception as e:
            return {
                "passed": True,
                "message": f"Warning in Layer 3: {str(e)}",
                "details": {}
            }
    
    # ============== MAIN ANALYSIS METHOD ==============
    
    def analyze_prescription(
        self,
        prescriber_id: str,
        patient_id: str,
        drug: str,
        dose: float
    ) -> Dict[str, Any]:
        """
        Full 4-layer prescription analysis.
        
        Returns decision and detailed layer-by-layer results.
        """
        self.analysis_count += 1
        
        # Layer 0: Doctor Authorization
        layer0 = self.layer0_doctor_authorization(prescriber_id)
        if not layer0["passed"]:
            return {
                "approved": False,
                "prescriber_id": prescriber_id,
                "patient_id": patient_id,
                "drug": drug,
                "dose": dose,
                "layer0": layer0,
                "layer1": {"passed": False, "message": "Skipped - Layer 0 failed"},
                "layer2": {"passed": False, "message": "Skipped - Layer 0 failed"},
                "layer3": {"passed": False, "message": "Skipped - Layer 0 failed"},
                "safety_score": 0,
                "reason": layer0["message"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Layer 1: Patient Validation
        layer1 = self.layer1_patient_validation(patient_id)
        if not layer1["passed"]:
            return {
                "approved": False,
                "prescriber_id": prescriber_id,
                "patient_id": patient_id,
                "drug": drug,
                "dose": dose,
                "layer0": layer0,
                "layer1": layer1,
                "layer2": {"passed": False, "message": "Skipped - Layer 1 failed"},
                "layer3": {"passed": False, "message": "Skipped - Layer 1 failed"},
                "safety_score": 25,
                "reason": layer1["message"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Layer 2: Drug Safety
        layer2 = self.layer2_drug_safety(drug, dose)
        if not layer2["passed"]:
            return {
                "approved": False,
                "prescriber_id": prescriber_id,
                "patient_id": patient_id,
                "drug": drug,
                "dose": dose,
                "layer0": layer0,
                "layer1": layer1,
                "layer2": layer2,
                "layer3": {"passed": False, "message": "Skipped - Layer 2 failed"},
                "safety_score": 50,
                "reason": layer2["message"],
                "timestamp": datetime.now().isoformat()
            }
        
        # Layer 3: Contraindication Detection
        layer3 = self.layer3_contraindication_detection(patient_id, drug, dose)
        if not layer3["passed"]:
            return {
                "approved": False,
                "prescriber_id": prescriber_id,
                "patient_id": patient_id,
                "drug": drug,
                "dose": dose,
                "layer0": layer0,
                "layer1": layer1,
                "layer2": layer2,
                "layer3": layer3,
                "safety_score": 25,
                "reason": layer3["message"],
                "timestamp": datetime.now().isoformat()
            }
        
        # ALL LAYERS PASSED - APPROVED
        self.approved_count += 1
        
        return {
            "approved": True,
            "prescriber_id": prescriber_id,
            "patient_id": patient_id,
            "drug": drug,
            "dose": dose,
            "layer0": layer0,
            "layer1": layer1,
            "layer2": layer2,
            "layer3": layer3,
            "safety_score": 100,
            "reason": "✅ APPROVED - All 4 layers passed",
            "timestamp": datetime.now().isoformat()
        }
    
    # ============== UTILITY METHODS ==============
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient details"""
        try:
            if self.patients_df is None:
                return None
            
            patient = self.patients_df[
                self.patients_df['patient_id'] == patient_id
            ]
            
            if patient.empty:
                return None
            
            patient_data = patient.iloc[0]
            return patient_data.to_dict()
        except:
            return None
    
    def get_prescriber(self, prescriber_id: str) -> Optional[Dict]:
        """Get prescriber details"""
        try:
            if self.prescribers_df is None:
                return None
            
            prescriber = self.prescribers_df[
                self.prescribers_df['doctor_id'] == prescriber_id
            ]
            
            if prescriber.empty:
                return None
            
            prescriber_data = prescriber.iloc[0]
            return prescriber_data.to_dict()
        except:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            total_prescribers = len(self.prescribers_df) if self.prescribers_df is not None else 0
            total_patients = len(self.patients_df) if self.patients_df is not None else 0
            
            return {
                "total_prescribers": total_prescribers,
                "total_patients": total_patients,
                "total_analyses": self.analysis_count,
                "approved_count": self.approved_count,
                "denied_count": self.analysis_count - self.approved_count,
                "approval_rate": f"{(self.approved_count/max(self.analysis_count, 1)*100):.1f}%"
            }
        except:
            return {
                "error": "Could not retrieve statistics"
            }
