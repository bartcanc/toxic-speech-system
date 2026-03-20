from fastapi import APIRouter, HTTPException
from schemas.ai_payloads import TextRequest, AnalysisResponse
from services.ai_engine import predict_toxicity

# Tworzymy niezależny router
router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: TextRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Tekst nie może być pusty.")

    try:
        # Odpytujemy nasz niezależny silnik AI
        result = predict_toxicity(request.text)

        return AnalysisResponse(
            text=request.text,
            verdict=result["verdict"],
            confidence_percent=round(result["confidence"], 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy AI: {str(e)}")