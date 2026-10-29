# 파일 업로드 API 사용법 가이드

> ⚠️ **현재 미구현**: `/app/copd/file/upload`, `/app/copd/files/...`, `/app/copd/files/list/{USER_UUID}` 는
> 서버에 없습니다 (호출 시 404). 음성 업로드는 `/app/copd/voice/file`, `/app/copd/survey-voice` 를 사용하세요.

## 📁 파일 업로드 방법

### 1. 음성 파일 업로드 (전용)
```bash
curl -X POST "http://172.30.1.62:8000/app/copd/voice/file" \
  -F "file=@/path/to/voice.wav" \
  -F "USER_UUID=SS00001" \
  -F "patient_id=P001" \
  -F "voice_quality=high" \
  -F "transcription=안녕하세요 테스트입니다" \
  -F "analysis_result=정상 음성 패턴"
```

### 2. 범용 파일 업로드
```bash
# 음성 파일
curl -X POST "http://172.30.1.62:8000/app/copd/file/upload" \
  -F "file=@voice_sample.wav" \
  -F "USER_UUID=SS00001" \
  -F "file_type=voice" \
  -F "description=환자 음성 샘플" \
  -F "metadata={\"quality\":\"high\",\"duration\":45.2}"

# 이미지 파일  
curl -X POST "http://172.30.1.62:8000/app/copd/file/upload" \
  -F "file=@chest_xray.jpg" \
  -F "USER_UUID=SS00001" \
  -F "file_type=image" \
  -F "description=흉부 X-ray 이미지"

# 문서 파일
curl -X POST "http://172.30.1.62:8000/app/copd/file/upload" \
  -F "file=@medical_report.pdf" \
  -F "USER_UUID=SS00001" \
  -F "file_type=document" \
  -F "description=의료진 소견서"
```

### 3. 파일 목록 조회
```bash
# 특정 환자의 모든 파일
curl "http://172.30.1.62:8000/app/copd/files/list/SS00001"

# 특정 타입의 파일만
curl "http://172.30.1.62:8000/app/copd/files/list/SS00001?file_type=voice"
```

### 4. 파일 다운로드
```bash
curl "http://172.30.1.62:8000/app/copd/files/voice/20240924/SS00001_20240924_123456_abc12345.wav" \
  -o downloaded_file.wav
```

## 🛠️ Python으로 파일 업로드

```python
import requests

def upload_voice_file():
    url = "http://172.30.1.62:8000/app/copd/voice/file"
    
    with open("voice_sample.wav", "rb") as f:
        files = {"file": f}
        data = {
            "USER_UUID": "SS00001",
            "patient_id": "P001",
            "voice_quality": "high",
            "transcription": "테스트 음성입니다.",
            "analysis_result": "정상 패턴"
        }
        response = requests.post(url, files=files, data=data)
    
    return response.json()

def upload_general_file():
    url = "http://172.30.1.62:8000/app/copd/file/upload"
    
    with open("document.pdf", "rb") as f:
        files = {"file": f}
        data = {
            "USER_UUID": "SS00001",
            "file_type": "document",
            "description": "의료 보고서",
            "metadata": '{"category": "report", "urgent": true}'
        }
        response = requests.post(url, files=files, data=data)
    
    return response.json()

def get_file_list():
    url = "http://172.30.1.62:8000/app/copd/files/list/SS00001"
    response = requests.get(url)
    return response.json()
```

## 📋 파일 타입별 제한사항

### 음성 파일 (voice)
- **최대 크기**: 50MB
- **허용 형식**: .wav, .mp3, .m4a, .ogg, .flac
- **저장 위치**: `/workspace/8889/files/voice/YYYYMMDD/`

### 이미지 파일 (image)  
- **최대 크기**: 10MB
- **허용 형식**: .jpg, .jpeg, .png, .gif, .bmp, .webp
- **저장 위치**: `/workspace/8889/files/image/YYYYMMDD/`

### 문서 파일 (document)
- **최대 크기**: 20MB
- **허용 형식**: .pdf, .doc, .docx, .txt, .csv, .xlsx
- **저장 위치**: `/workspace/8889/files/document/YYYYMMDD/`

### 기타 파일 (other)
- **최대 크기**: 100MB
- **허용 형식**: 모든 형식
- **저장 위치**: `/workspace/8889/files/other/YYYYMMDD/`

## 📁 디렉토리 구조
```
/workspace/8889/
├── files/
│   ├── voice/
│   │   └── 20240924/
│   │       ├── SS00001_20240924_123456_abc12345.wav
│   │       └── SS00001_20240924_123456_abc12345.wav.metadata.json
│   ├── image/
│   │   └── 20240924/
│   ├── document/
│   │   └── 20240924/
│   └── other/
│       └── 20240924/
└── copd_data/          # JSON 데이터 저장소
    └── basic_SS00001_20240924_123456.json
```

## 🔒 보안 기능
- 안전한 파일명 생성 (UUID 포함)
- 파일 크기 제한
- 확장자 검증  
- 날짜별 폴더 분리
- 메타데이터 별도 저장