from typing import Union
from fastapi import FastAPI
from app.routers import basic, oximeter, chair_stand, survey, survey_voice, voice

app = FastAPI(
    title="COPD Patient Assessment API",
    description="COPD 환자 평가 및 삼성헬스 바이탈 데이터 수집 API",
    version="2.0.0"
)

# 기본 엔드포인트
@app.get("/")
def read_root():
    return {
        "message": "COPD Patient Assessment API",
        "version": "2.0.0",
        "endpoints": {
            "copd_assessment": [
                "/app/copd/basic",
                "/app/copd/oximeter", 
                "/app/copd/chair-stand",
                "/app/copd/survey-voice",
                "/app/copd/survey",
                "/app/copd/voice",
                "/app/copd/voice/file"
            ]
        }
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

# COPD 환자 평가 라우터 등록
app.include_router(basic.router, prefix="/app/copd", tags=["COPD Assessment"])
app.include_router(oximeter.router, prefix="/app/copd", tags=["COPD Assessment"])
app.include_router(chair_stand.router, prefix="/app/copd", tags=["COPD Assessment"])
app.include_router(survey.router, prefix="/app/copd", tags=["COPD Assessment"])
app.include_router(survey_voice.router, prefix="/app/copd", tags=["COPD Assessment"])
app.include_router(voice.router, prefix="/app/copd", tags=["COPD Assessment"])
