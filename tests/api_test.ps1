<#
COPD API 기능 테스트 (PowerShell 5+/7, curl.exe 필요)

  .\tests\api_test.ps1                                   # 외부 주소, USER_UUID=TEST0000
  .\tests\api_test.ps1 -Base http://172.30.1.62:8000     # 내부망
  .\tests\api_test.ps1 -Uuid SS0001

테스트 데이터가 서버 ./data/<Uuid>/ 에 실제로 저장된다. 끝나면 서버에서 삭제:
  rm -r ~/Downloads/doctor-dairy-COPD-API/data/<Uuid>
#>
param([string]$Base = "http://14.63.89.203:18000", [string]$Uuid = "TEST0000")
$ErrorActionPreference = 'Stop'
$dir = Join-Path ([IO.Path]::GetTempPath()) 'copd_api_test'
New-Item -ItemType Directory -Force $dir | Out-Null

# 1초 16kHz mono 16bit 440Hz wav 생성
function New-Wav($path) {
    $sr = 16000; $n = $sr; $data = New-Object byte[] ($n * 2)
    for ($i = 0; $i -lt $n; $i++) {
        $v = [int16](8000 * [Math]::Sin(2 * [Math]::PI * 440 * $i / $sr))
        $b = [BitConverter]::GetBytes($v); $data[2*$i] = $b[0]; $data[2*$i+1] = $b[1]
    }
    $ms = New-Object IO.MemoryStream; $w = New-Object IO.BinaryWriter $ms
    $w.Write([Text.Encoding]::ASCII.GetBytes('RIFF')); $w.Write([int](36 + $data.Length))
    $w.Write([Text.Encoding]::ASCII.GetBytes('WAVEfmt ')); $w.Write([int]16); $w.Write([int16]1); $w.Write([int16]1)
    $w.Write([int]$sr); $w.Write([int]($sr * 2)); $w.Write([int16]2); $w.Write([int16]16)
    $w.Write([Text.Encoding]::ASCII.GetBytes('data')); $w.Write([int]$data.Length); $w.Write($data)
    [IO.File]::WriteAllBytes($path, $ms.ToArray())
}
foreach ($f in 'pre_ah','post_ah','pre_paragraph','post_paragraph') { New-Wav (Join-Path $dir "$f.wav") }
Set-Content (Join-Path $dir 'bad.pdf') 'not audio'

$results = @()
function Add-Result($name, $expect, $got, $body) {
    $ok = "$got" -eq "$expect"
    $script:results += [pscustomobject]@{ Case = $name; Expect = $expect; Got = $got; Pass = $ok }
    Write-Host ("[{0}] {1}  expect={2} got={3}" -f ($(if ($ok) { 'PASS' } else { 'FAIL' })), $name, $expect, $got)
    if ($body) { Write-Host ("    " + $body.Substring(0, [Math]::Min(400, $body.Length))) }
}
function Invoke-Case($name, $expect, [string[]]$curlArgs) {
    $out = & curl.exe -s -m 30 -w "`n__HTTP__%{http_code}" @curlArgs 2>&1 | Out-String
    $code = if ($out -match '__HTTP__(\d+)') { [int]$Matches[1] } else { 0 }
    $body = ($out -replace '\s*__HTTP__\d+\s*$', '').Trim()
    Add-Result $name $expect $code $body
    return $body
}
function Json($name, $expect, $path, $obj) {
    $f = Join-Path $dir ("body_" + ($name -replace '\W', '_') + ".json")
    [IO.File]::WriteAllText($f, ($obj | ConvertTo-Json -Depth 5 -Compress), (New-Object Text.UTF8Encoding $false))
    Invoke-Case $name $expect @('-X', 'POST', "$Base$path", '-H', 'Content-Type: application/json', '--data-binary', "@$f")
}
$w = { param($n) "@" + (Join-Path $dir "$n.wav") + ";type=audio/wav" }

"=== 정상 케이스 ($Base, USER_UUID=$Uuid)"
$root = Invoke-Case 'GET /' 200 @("$Base/")
$null = Json 'basic' 200 '/app/copd/basic' @{ USER_UUID = $Uuid; data = @{ sex = 1; birth = '1970-05-15'; height = 175.5; weight = 70.2; education = 4 } }
$null = Json 'oximeter' 200 '/app/copd/oximeter' @{ USER_UUID = $Uuid; data = @{ pre_HR = 72.5; pre_SpO2 = 98.2; post_HR = 85.3; post_SpO2 = 96.8 } }
$null = Json 'chair-stand' 200 '/app/copd/chair-stand' @{ USER_UUID = $Uuid; data = @{ CS_count = 15.0 } }
$null = Json 'survey' 200 '/app/copd/survey' @{ USER_UUID = $Uuid; data = @{ CAT1 = 2; CAT2 = 1; CAT3 = 0; CAT4 = 3; CAT5 = 2; CAT6 = 1; CAT7 = 0; CAT8 = 1; CAT_sum = 10; mMRC = 2; Smoke_CAT1 = 1; Smoke_CAT2 = 2; Smoke_CAT3 = 3; Smoke_CAT4 = 10.5 } }
$null = Invoke-Case 'survey-voice' 200 @('-X', 'POST', "$Base/app/copd/survey-voice",
    '-F', "USER_UUID=$Uuid", '-F', 'MBS=5', '-F', 'Borg_RPE=12',
    '-F', "voice_pre_ah=$(& $w pre_ah)", '-F', "voice_post_ah=$(& $w post_ah)",
    '-F', "voice_pre_paragraph=$(& $w pre_paragraph)", '-F', "voice_post_paragraph=$(& $w post_paragraph)",
    '-F', 'transcription_pre_ah=아~', '-F', 'transcription_post_ah=아~',
    '-F', 'transcription_pre_paragraph=가을이 되니 산에 단풍이 들었습니다', '-F', 'transcription_post_paragraph=바람이 불어 나뭇잎이 떨어집니다')
$v1 = Json 'voice (json, deprecated)' 200 '/app/copd/voice' @{ USER_UUID = $Uuid; data = @{ voice_file_path = '/tmp/test.wav'; transcription = '테스트' } }
$v2 = Invoke-Case 'voice/file' 200 @('-X', 'POST', "$Base/app/copd/voice/file", '-F', "USER_UUID=$Uuid", '-F', "file=$(& $w pre_ah)", '-F', 'transcription=아~')

"=== 회귀 검사"
# 같은 초에 저장해도 파일명이 겹치지 않아야 한다 (예전엔 초 단위라 덮어씀)
$p1 = try { ($v1 | ConvertFrom-Json).filepath } catch { $null }
$p2 = try { ($v2 | ConvertFrom-Json).filepath } catch { $null }
Add-Result 'voice / voice/file 저장 경로 다름' 'True' ([bool]($p1 -and $p2 -and $p1 -ne $p2)) "$p1 | $p2"
# 같은 data_type 연속 전송 → 두 번째는 _1 등 다른 경로여야 한다
$cs = @{ USER_UUID = $Uuid; data = @{ CS_count = 3.0 } }
$c1 = try { ((Json 'chair-stand 연속 #1' 200 '/app/copd/chair-stand' $cs) | ConvertFrom-Json).filepath } catch { $null }
$c2 = try { ((Json 'chair-stand 연속 #2' 200 '/app/copd/chair-stand' $cs) | ConvertFrom-Json).filepath } catch { $null }
Add-Result 'chair-stand 연속 저장 경로 다름' 'True' ([bool]($c1 -and $c2 -and $c1 -ne $c2)) "$c1 | $c2"
# GET / 이 안내하는 엔드포인트가 전부 실제로 존재해야 한다
$listed = @(($root | ConvertFrom-Json).endpoints.PSObject.Properties.Value | % { $_ })
$paths = @((Invoke-RestMethod "$Base/openapi.json").paths.PSObject.Properties.Name)
$missing = @($listed | ? { $_ -notin $paths })
Add-Result 'GET / 안내 엔드포인트 모두 존재' 'True' ($missing.Count -eq 0) ($(if ($missing) { "없음: " + ($missing -join ', ') }))

"=== 오류 케이스 (검증이 제대로 거부하는지)"
$null = Json 'basic sex=3' 422 '/app/copd/basic' @{ USER_UUID = $Uuid; data = @{ sex = 3; birth = '1970-05-15'; height = 175.5; weight = 70.2; education = 4 } }
$null = Json 'basic height 누락' 422 '/app/copd/basic' @{ USER_UUID = $Uuid; data = @{ sex = 1; birth = '1970-05-15'; weight = 70.2; education = 4 } }
$null = Json 'chair-stand CS_count=-1' 422 '/app/copd/chair-stand' @{ USER_UUID = $Uuid; data = @{ CS_count = -1 } }
$null = Json 'survey CAT1=6' 422 '/app/copd/survey' @{ USER_UUID = $Uuid; data = @{ CAT1 = 6; CAT2 = 1; CAT3 = 0; CAT4 = 3; CAT5 = 2; CAT6 = 1; CAT7 = 0; CAT8 = 1; CAT_sum = 10; mMRC = 2; Smoke_CAT1 = 1; Smoke_CAT2 = 2; Smoke_CAT3 = 3; Smoke_CAT4 = 10.5 } }
$null = Invoke-Case 'survey-voice MBS=11' 422 @('-X', 'POST', "$Base/app/copd/survey-voice",
    '-F', "USER_UUID=$Uuid", '-F', 'MBS=11', '-F', 'Borg_RPE=12',
    '-F', "voice_pre_ah=$(& $w pre_ah)", '-F', "voice_post_ah=$(& $w post_ah)",
    '-F', "voice_pre_paragraph=$(& $w pre_paragraph)", '-F', "voice_post_paragraph=$(& $w post_paragraph)")
$null = Invoke-Case 'survey-voice 파일 1개 누락' 422 @('-X', 'POST', "$Base/app/copd/survey-voice",
    '-F', "USER_UUID=$Uuid", '-F', 'MBS=5', '-F', 'Borg_RPE=12',
    '-F', "voice_pre_ah=$(& $w pre_ah)", '-F', "voice_post_ah=$(& $w post_ah)", '-F', "voice_pre_paragraph=$(& $w pre_paragraph)")
$null = Invoke-Case 'voice/file pdf 업로드' 400 @('-X', 'POST', "$Base/app/copd/voice/file", '-F', "USER_UUID=$Uuid", '-F', "file=@$(Join-Path $dir 'bad.pdf');type=application/pdf")

"=== 요약"
$results | Format-Table -AutoSize | Out-String
$pass = @($results | ? Pass).Count
"PASS {0}/{1}" -f $pass, $results.Count
if ($pass -ne $results.Count) { exit 1 }
