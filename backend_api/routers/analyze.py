from fastapi import APIRouter, HTTPException
from schemas.ai_payloads import TextRequest, AnalysisResponse, AIResults, ConfidenceScores
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

        confidence_obj = ConfidenceScores(
            toxic=result["confidence_scores"]["hejt"],
            scam=result["confidence_scores"]["scam"],
            grooming=result["confidence_scores"]["grooming"]
        )

        results_obj = AIResults(
            is_safe=result["is_safe"],
            detected_flags=result["detected_flags"],
            confidence_scores=confidence_obj
        )

        return AnalysisResponse(
            status="success",
            text_analyzed=request.text,
            results=results_obj
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy AI: {str(e)}")