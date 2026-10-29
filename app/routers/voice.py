from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models import VoiceRequest
from app.services import data_service
import os
import shutil
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/voice")
async def upload_voice_data(data: VoiceRequest):
    """음성 데이터 (파일 경로, 전사 텍스트, 분석 결과) 업로드"""
    return data_service.save_data(data)

@router.post("/voice/file")
async def upload_voice_file(
    file: UploadFile = File(..., description="음성 파일"),
    USER_UUID: str = Form(..., description="환자 식별자"),
    transcription: Optional[str] = Form(None, description="음성 전사 텍스트"),
):
    """음성 파일 직접 업로드 및 메타데이터 저장"""
    
    # 파일 크기 제한 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기가 너무 큽니다. (최대 50MB)")
    
    # 파일 형식 검증
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 허용 형식: {', '.join(allowed_extensions)}"
            )
    
    # 업로드 디렉토리 설정 (USER_UUID 중심)
    upload_dir = os.path.join(".", "data", USER_UUID)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 파일명: YYYYMMDD_timestamp_*.*
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    timestamp = now.strftime("%H%M%S%f")
    safe_filename = f"{date_part}_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 파일 크기로 대략적인 길이 추정 (실제로는 음성 분석 라이브러리 사용 권장)
        file_size = os.path.getsize(file_path)
        estimated_duration = file_size / 32000  # 대략적인 추정값
        
        # VoiceRequest 객체 생성
        from app.models import VoiceData
        voice_data = VoiceData(
            voice_file_path=file_path,
            transcription=transcription
        )
        
        voice_request = VoiceRequest(
            USER_UUID=USER_UUID,
            data=voice_data
        )
        
        # 데이터 저장
        result = data_service.save_data(voice_request)
        result["uploaded_file"] = file.filename
        result["file_path"] = file_path
        
        return result
        
    except Exception as e:
        # 에러 발생 시 파일 정리
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")
    
    finally:
        await file.close()