import json
import os
from datetime import datetime


def _extract_user_uuid(data):
    user_uuid = getattr(data, "USER_UUID", None)
    if user_uuid:
        return user_uuid

    if hasattr(data, "dict"):
        payload = data.dict()
        return payload.get("USER_UUID", "unknown")

    return "unknown"


def _extract_data_type(data):
    explicit_type = getattr(data, "DATA_TYPE", None)
    if explicit_type:
        return explicit_type

    type_mapping = {
        "BasicInfoRequest": "basic",
        "OximeterRequest": "oximeter",
        "ChairStandRequest": "chair-stand",
        "SurveyVoiceRequest": "survey-voice",
        "SurveyRequest": "survey",
        "VoiceRequest": "voice",
    }
    return type_mapping.get(type(data).__name__, "unknown")


def save_data(data):
    # USER_UUID 중심 저장 디렉토리 생성
    base_dir = os.path.join(".", "data")
    user_uuid = _extract_user_uuid(data)
    save_dir = os.path.join(base_dir, user_uuid)
    os.makedirs(save_dir, exist_ok=True)

    # 파일명: YYYYMMDD_timestamp_data_type.json
    data_type = _extract_data_type(data)
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    timestamp = now.strftime("%H%M%S%f")
    filename = f"{date_part}_{timestamp}_{data_type}.json"
    filepath = os.path.join(save_dir, filename)

    # Pydantic 모델을 dict로 변환 후 저장
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data.dict(), f, ensure_ascii=False, indent=2)

    return {"result": "success", "filepath": filepath}