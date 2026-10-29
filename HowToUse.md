# COPD 환자 평가 API 사용 가이드

COPD(만성폐쇄성폐질환) 환자의 기본정보, 설문조사, 신체측정, 음성 데이터를 수집하는 API입니다.

---

## 서버 정보
- **서버 주소**: `http://14.63.89.203:18000`
- **API 경로**: `/app/copd/{데이터타입}`
- **요청 방식**: `POST`

---

## 지원 데이터 타입

| 데이터 타입 | 엔드포인트 | 설명 |
|------------|-----------|------|
| 기본정보 | `/app/copd/basic` | 성별, 생년월일, 키, 몸무게, 교육수준 |
| 산소포화도 | `/app/copd/oximeter` | 운동 전후 심박수, 산소포화도 |
| 의자 일어서기 | `/app/copd/chair-stand` | 30초간 의자 일어서기 횟수 |
| 설문조사+음성 | `/app/copd/survey-voice` | MBS, Borg RPE + 4개 음성 파일 |
| 설문조사 | `/app/copd/survey` | CAT 8문항, mMRC, 흡연 관련 |

### 음성 데이터 구성 (4개 필수)
- Chair Standing 전 "아~" 소리
- Chair Standing 후 "아~" 소리
- Chair Standing 전 문단 읽기
- Chair Standing 후 문단 읽기

---

## API 엔드포인트

### 1. 기본정보 업로드

환자의 기본 신체정보를 전송합니다.

**엔드포인트**: `POST /app/copd/basic`

**요청 예제**:
```bash
curl -X POST "http://14.63.89.203:18000/app/copd/basic" \
  -H "Content-Type: application/json" \
  -d '{
    "USER_UUID": "SS00001",
    "data": {
      "sex": 1,
      "birth": "1970-05-15",
      "height": 175.5,
      "weight": 70.2,
      "education": 4
    }
  }'
```

**파라미터**:
- `sex`: 성별 (1=남성, 2=여성)
- `birth`: 생년월일 (YYYY-MM-DD)
- `height`: 키 (cm)
- `weight`: 몸무게 (kg)
- `education`: 교육수준 (1~6)

---

### 2. 산소포화도 측정 업로드

운동 전후의 심박수와 산소포화도를 전송합니다.

**엔드포인트**: `POST /app/copd/oximeter`

**요청 예제**:
```bash
curl -X POST "http://14.63.89.203:18000/app/copd/oximeter" \
  -H "Content-Type: application/json" \
  -d '{
    "USER_UUID": "SS00001",
    "data": {
      "pre_HR": 72.5,
      "pre_SpO2": 98.2,
      "post_HR": 85.3,
      "post_SpO2": 96.8
    }
  }'
```

**파라미터**:
- `pre_HR`: 운동 전 심박수 (bpm)
- `pre_SpO2`: 운동 전 산소포화도 (%)
- `post_HR`: 운동 후 심박수 (bpm)
- `post_SpO2`: 운동 후 산소포화도 (%)

---

### 3. 의자 일어서기 검사 업로드

30초간 의자에서 일어선 횟수를 전송합니다.

**엔드포인트**: `POST /app/copd/chair-stand`

**요청 예제**:
```bash
curl -X POST "http://14.63.89.203:18000/app/copd/chair-stand" \
  -H "Content-Type: application/json" \
  -d '{
    "USER_UUID": "SS00001",
    "data": {
      "CS_count": 15.0
    }
  }'
```

**파라미터**:
- `CS_count`: 30초간 의자 일어서기 횟수

---

### 4. 설문조사 + 음성 데이터 업로드

MBS, Borg RPE 설문 데이터와 4개의 음성 파일을 함께 전송합니다.

**엔드포인트**: `POST /app/copd/survey-voice`

**Content-Type**: `multipart/form-data`

**요청 예제**:
```bash
curl -X POST "http://14.63.89.203:18000/app/copd/survey-voice" \
     -F "USER_UUID=SS00001" \
     -F "MBS=5" \
     -F "Borg_RPE=12" \
     -F "voice_pre_ah=@./pre_ah.wav" \
     -F "voice_post_ah=@./post_ah.wav" \
     -F "voice_pre_paragraph=@./pre_paragraph.wav" \
     -F "voice_post_paragraph=@./post_paragraph.wav" \
     -F "transcription_pre_ah=아~" \
     -F "transcription_post_ah=아~" \
     -F "transcription_pre_paragraph=가을이 되니 산에 단풍이 들었습니다" \
     -F "transcription_post_paragraph=바람이 불어 나뭇잎이 떨어집니다"
```

**필수 파라미터**:
- `USER_UUID`: 환자 ID (예: SS00001)
- `MBS`: Modified Borg Scale (0~10)
- `Borg_RPE`: Rate of Perceived Exertion (6~20)
- `voice_pre_ah`: Chair Standing 전 "아~" 소리 파일
- `voice_post_ah`: Chair Standing 후 "아~" 소리 파일
- `voice_pre_paragraph`: Chair Standing 전 문단 읽기 파일
- `voice_post_paragraph`: Chair Standing 후 문단 읽기 파일

**선택 파라미터**:
- `transcription_pre_ah`: 전 "아~" 소리 전사 텍스트
- `transcription_post_ah`: 후 "아~" 소리 전사 텍스트
- `transcription_pre_paragraph`: 전 문단 읽기 전사 텍스트
- `transcription_post_paragraph`: 후 문단 읽기 전사 텍스트

**주의사항**:
- 음성 파일은 wav, mp3, m4a 등 오디오 형식만 가능
- 각 파일 최대 크기: 50MB
- `@` 기호 뒤에 실제 파일 경로를 입력

---

### 5. 설문조사 (일반) 업로드

CAT 설문, mMRC, 흡연 관련 설문 데이터를 전송합니다.

**엔드포인트**: `POST /app/copd/survey`

**요청 예제**:
```bash
curl -X POST "http://14.63.89.203:18000/app/copd/survey" \
  -H "Content-Type: application/json" \
  -d '{
    "USER_UUID": "SS00001",
    "data": {
      "CAT1": 2, "CAT2": 1, "CAT3": 0, "CAT4": 3,
      "CAT5": 2, "CAT6": 1, "CAT7": 0, "CAT8": 1,
      "CAT_sum": 10,
      "mMRC": 2,
      "Smoke_CAT1": 1,
      "Smoke_CAT2": 2,
      "Smoke_CAT3": 3,
      "Smoke_CAT4": 10.5
    }
  }'
```

**파라미터**:
- `CAT1~CAT8`: CAT 설문 각 문항 (0~5)
- `CAT_sum`: CAT 총합 (0~40)
- `mMRC`: Modified Medical Research Council (0~4)
- `Smoke_CAT1`: 흡연 유무 (1~2)
- `Smoke_CAT2`: 금연 여부 (1~3)
- `Smoke_CAT3`: 금연 기간 (1~4)
- `Smoke_CAT4`: 흡연량 (연속값)

---

## 응답 형식

### 성공 응답

성공 시 HTTP 200 과 함께 `result`, 저장된 JSON 경로 `filepath` 를 반환합니다.

`basic`, `oximeter`, `chair-stand`, `survey`:
```json
{
  "result": "success",
  "filepath": "./data/SS00001/20250121_143052_basic.json"
}
```

`survey-voice` (업로드한 원본 파일명과 서버 저장 경로 추가):
```json
{
  "result": "success",
  "filepath": "./data/SS00001/20250121_143052_survey-voice.json",
  "uploaded_files": {
    "voice_pre_ah": "pre_ah.wav",
    "voice_post_ah": "post_ah.wav",
    "voice_pre_paragraph": "pre_paragraph.wav",
    "voice_post_paragraph": "post_paragraph.wav"
  },
  "file_paths": {
    "voice_pre_ah": "./data/SS00001/20250121_143052_pre_ah_a1b2c3d4.wav",
    "voice_post_ah": "./data/SS00001/20250121_143052_post_ah_e5f6g7h8.wav",
    "voice_pre_paragraph": "./data/SS00001/20250121_143052_paragraph_1_i9j0k1l2.wav",
    "voice_post_paragraph": "./data/SS00001/20250121_143052_paragraph_2_m3n4o5p6.wav"
  }
}
```

`voice/file`:
```json
{
  "result": "success",
  "filepath": "./data/SS00001/20250121_143052_voice.json",
  "uploaded_file": "pre_ah.wav",
  "file_path": "./data/SS00001/20250121_143052_a1b2c3d4.wav"
}
```

### 오류 응답

#### 파라미터 검증 오류
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "MBS"],
      "msg": "Input should be less than or equal to 10",
      "input": "11",
      "ctx": {"le": 10}
    }
  ]
}
```

#### 파일 형식 오류
```json
{
  "detail": "파일 'document.pdf': 지원하지 않는 파일 형식입니다. 허용 형식: .wav, .mp3, .m4a, .ogg, .flac"
}
```

#### 파일 크기 초과
```json
{
  "detail": "파일 'large_audio.wav' 크기가 너무 큽니다. (최대 50MB)"
}
```

---

## 데이터 검증 규칙

### 정수형 (int) 파라미터
- 지정된 범위 내의 값만 허용 (예: 1~2, 0~5, 6~20)
- 범위를 벗어날 경우 검증 오류 반환

### 실수형 (float) 파라미터
- 양수 값 필수
- 연속형 데이터 (continuous)

### 문자열 (String) 파라미터
- 날짜 필드: ISO 8601 형식 (YYYY-MM-DD)
- 파일 경로: 절대 경로 또는 상대 경로

### 파일 업로드
- 지원 형식: wav, mp3, m4a, ogg, flac
- 최대 크기: 50MB/파일
- Content-Type: audio/*

---

## 문제 해결

### curl 명령어 실행 오류
Windows에서는 `curl.exe`를 사용하거나, Postman 같은 API 테스트 도구를 사용하세요.

### 파일 경로 오류
`@` 기호 뒤에는 실제 파일이 있는 전체 경로를 입력하세요.

```bash
# 현재 디렉토리의 파일
-F "voice_pre_ah=@pre_ah.wav"

# 절대 경로 (Unix/Mac)
-F "voice_pre_ah=@/Users/username/Desktop/pre_ah.wav"

# 절대 경로 (Windows)
-F "voice_pre_ah=@C:/Users/username/Desktop/pre_ah.wav"
```

### JSON 형식 오류
JSON 데이터는 큰따옴표(`"`)를 사용해야 하며, 마지막 항목에는 쉼표를 붙이지 않습니다.

### 서버 연결 오류
서버 주소(`http://14.63.89.203:18000`)가 정확한지, 네트워크 연결이 정상인지 확인하세요.

---

## 저장 위치

**파일 저장 경로**: `./data/USER_UUID/`

**파일명 형식**:
- 음성 파일: `YYYYMMDD_HHMMSS_{file_type}_{random_id}.{extension}`
- JSON 메타데이터: `YYYYMMDD_HHMMSS_{data_type}.json`
- 같은 초에 같은 데이터 타입이 다시 오면 `YYYYMMDD_HHMMSS_{data_type}_1.json`, `_2` ... 로 저장 (덮어쓰지 않음)

**예시**:
- `20250121_143052_pre_ah_a1b2c3d4.wav`
- `20250121_143055_post_ah_e5f6g7h8.wav`
- `20250121_143058_paragraph_1_i9j0k1l2.wav`
- `20250121_143101_paragraph_2_m3n4o5p6.wav`
- `20250121_143102_basic.json`

---

**마지막 업데이트**: 2025년 10월 21일
````

---
