from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models import SurveyVoiceRequest, SingleVoiceFile, SurveyVoiceData
from app.services import data_service
import os
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/survey-voice")
async def upload_survey_voice_data(
    USER_UUID: str = Form(..., description="환자 식별자"),
    MBS: int = Form(..., ge=0, le=10, description="Modified Borg Scale: 0~10"),
    Borg_RPE: int = Form(..., ge=6, le=20, description="Rate of Perceived Exertion: 6~20"),
    voice_pre_ah: UploadFile = File(..., description="Chair Standing 전 '아~' 소리 파일"),
    voice_post_ah: UploadFile = File(..., description="Chair Standing 후 '아~' 소리 파일"),
    voice_pre_paragraph: UploadFile = File(..., description="문단 읽기 1 파일"),
    voice_post_paragraph: UploadFile = File(..., description="문단 읽기 2 파일"),
    transcription_pre_ah: Optional[str] = Form(None, description="Chair Standing 전 전사 텍스트"),
    transcription_post_ah: Optional[str] = Form(None, description="Chair Standing 후 전사 텍스트"),
    transcription_pre_paragraph: Optional[str] = Form(None, description="문단 읽기 1 전사 텍스트"),
    transcription_post_paragraph: Optional[str] = Form(None, description="문단 읽기 2 전사 텍스트"),
):
    """설문조사 음성 데이터 (MBS, Borg RPE) + 4개의 음성 파일 업로드"""
    
    # 파일 크기 제한 (각 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    voice_files = [voice_pre_ah, voice_post_ah, voice_pre_paragraph, voice_post_paragraph]
    
    for file in voice_files:
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"파일 '{file.filename}' 크기가 너무 큽니다. (최대 50MB)"
            )
    
    # 파일 형식 검증
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
    
    for file in voice_files:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if not file.content_type or not file.content_type.startswith('audio/'):
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"파일 '{file.filename}': 지원하지 않는 파일 형식입니다. 허용 형식: {', '.join(allowed_extensions)}"
                )
    
    # 업로드 디렉토리 설정 (USER_UUID 중심)
    upload_dir = os.path.join(".", "data", USER_UUID)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 파일 저장 함수
    async def save_voice_file(file: UploadFile, file_type: str, transcription: Optional[str]) -> SingleVoiceFile:
        now = datetime.now()
        date_part = now.strftime("%Y%m%d")
        timestamp = now.strftime("%H%M%S%f")
        file_extension = os.path.splitext(file.filename)[1].lower()
        safe_filename = f"{date_part}_{timestamp}_{file_type}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        try:
            # 파일 내용을 읽어서 저장
            contents = await file.read()
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            
            return SingleVoiceFile(
                voice_file_path=file_path,
                transcription=transcription
            )
        except Exception as e:
            # 에러 발생 시 파일 정리
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"파일 '{file.filename}' 업로드 실패: {str(e)}")
    
    try:
        # 4개의 음성 파일 저장
        voice_pre_ah_data = await save_voice_file(voice_pre_ah, "pre_ah", transcription_pre_ah)
        voice_post_ah_data = await save_voice_file(voice_post_ah, "post_ah", transcription_post_ah)
        voice_pre_paragraph_data = await save_voice_file(voice_pre_paragraph, "paragraph_1", transcription_pre_paragraph)
        voice_post_paragraph_data = await save_voice_file(voice_post_paragraph, "paragraph_2", transcription_post_paragraph)
        
        # SurveyVoiceData 객체 생성
        survey_voice_data = SurveyVoiceData(
            MBS=MBS,
            Borg_RPE=Borg_RPE,
            voice_pre_ah=voice_pre_ah_data,
            voice_post_ah=voice_post_ah_data,
            voice_pre_paragraph=voice_pre_paragraph_data,
            voice_post_paragraph=voice_post_paragraph_data
        )
        
        # SurveyVoiceRequest 객체 생성
        survey_voice_request = SurveyVoiceRequest(
            USER_UUID=USER_UUID,
            data=survey_voice_data
        )
        
        # 데이터 저장
        result = data_service.save_data(survey_voice_request)
        result["uploaded_files"] = {
            "voice_pre_ah": voice_pre_ah.filename,
            "voice_post_ah": voice_post_ah.filename,
            "voice_pre_paragraph": voice_pre_paragraph.filename,
            "voice_post_paragraph": voice_post_paragraph.filename
        }
        result["file_paths"] = {
            "voice_pre_ah": voice_pre_ah_data.voice_file_path,
            "voice_post_ah": voice_post_ah_data.voice_file_path,
            "voice_pre_paragraph": voice_pre_paragraph_data.voice_file_path,
            "voice_post_paragraph": voice_post_paragraph_data.voice_file_path
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 처리 실패: {str(e)}")