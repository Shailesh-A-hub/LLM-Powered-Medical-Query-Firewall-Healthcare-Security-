"""
Medical Prescription Firewall - FastAPI Backend
Main application server with 4-layer safety analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
from firewall_engine import PrescriptionFirewall

# Initialize FastAPI app
app = FastAPI(
    title="Medical Prescription Firewall",
    description="4-Layer Clinical Decision Support System",
    version="3.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize firewall engine
firewall = PrescriptionFirewall()

# ============== Pydantic Models ==============

class PrescriptionRequest(BaseModel):
    """Request model for prescription analysis"""
    prescriber_id: str
    patient_id: str
    drug: str
    dose: float


class LayerResult(BaseModel):
    """Result for individual firewall layer"""
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    approved: bool
    prescriber_id: str
    patient_id: str
    drug: str
    dose: float
    layer0: LayerResult
    layer1: LayerResult
    layer2: LayerResult
    layer3: LayerResult
    safety_score: int
    reason: str
    timestamp: str


class PatientProfile(BaseModel):
    """Patient information"""
    patient_id: str
    name: str
    age: int
    conditions: List[str]
    medications: List[str]
    liver_status: str
    kidney_status: str


class PrescriberProfile(BaseModel):
    """Prescriber information"""
    prescriber_id: str
    name: str
    specialty: str
    status: str
    dea_number: str
    license_number: str


# ============== Main Endpoints ==============

@app.post("/analyze-prescription", response_model=AnalysisResponse)
async def analyze_prescription(request: PrescriptionRequest):
    """
    Analyze prescription through 4-layer firewall.
    
    Returns:
    - Layer 0: Doctor authorization
    - Layer 1: Patient validation
    - Layer 2: Drug safety
    - Layer 3: Contraindication detection
    """
    try:
        result = firewall.analyze_prescription(
            prescriber_id=request.prescriber_id,
            patient_id=request.patient_id,
            drug=request.drug,
            dose=request.dose
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient profile by ID"""
    try:
        patient = firewall.get_patient(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/prescribers/{prescriber_id}")
async def get_prescriber(prescriber_id: str):
    """Get prescriber profile by ID"""
    try:
        prescriber = firewall.get_prescriber(prescriber_id)
        if not prescriber:
            raise HTTPException(status_code=404, detail="Prescriber not found")
        return prescriber
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        stats = firewall.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bulk-analyze")
async def bulk_analyze(requests: List[PrescriptionRequest]):
    """Analyze multiple prescriptions"""
    results = []
    for req in requests:
        try:
            result = firewall.analyze_prescription(
                prescriber_id=req.prescriber_id,
                patient_id=req.patient_id,
                drug=req.drug,
                dose=req.dose
            )
            results.append(result)
        except Exception as e:
            results.append({
                "error": str(e),
                "request": req.dict()
            })
    return results


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "service": "Medical Prescription Firewall"
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Medical Prescription Firewall API",
        "version": "3.0.0",
        "description": "4-Layer Clinical Decision Support System",
        "endpoints": {
            "POST /analyze-prescription": "Analyze single prescription",
            "POST /bulk-analyze": "Analyze multiple prescriptions",
            "GET /patients/{id}": "Get patient profile",
            "GET /prescribers/{id}": "Get prescriber profile",
            "GET /stats": "Get system statistics",
            "GET /health": "Health check",
            "GET /docs": "API documentation (Swagger UI)"
        }
    }


# ============== Error Handlers ==============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


# ============== Startup/Shutdown Events ==============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Medical Prescription Firewall API Starting...")
    print("📊 Loading prescriber and patient data...")
    firewall.initialize()
    print("✅ System Ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Medical Prescription Firewall API Shutting Down...")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("Medical Prescription Firewall - Backend Server")
    print("=" * 50)
    print("🏥 Healthcare Safety System")
    print("📍 Starting on http://0.0.0.0:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
