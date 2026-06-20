# TikTok 바이럴 영상 자동 다운로더

`yt-dlp` 기반 TikTok 영상 일괄 다운로드 스크립트입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 1. URL 목록 파일로 100개 다운로드
```bash
# urls.txt 에 URL을 한 줄씩 입력 후:
python3 downloader.py --urls urls.txt --count 100
```

### 2. 특정 계정의 영상 100개 다운로드
```bash
python3 downloader.py --user 계정이름 --count 100
```

### 3. 해시태그 기반 100개 다운로드
```bash
python3 downloader.py --hashtag funny --count 100
```

### 4. 단일 URL 다운로드
```bash
python3 downloader.py --url https://www.tiktok.com/@user/video/123456
```

### 5. 저장 폴더 지정
```bash
python3 downloader.py --user username --count 100 --output ./my_videos
```

### 6. 로그인이 필요한 경우 (쿠키 사용)
브라우저에서 쿠키를 Netscape 형식으로 export 후:
```bash
python3 downloader.py --user username --count 100 --cookies cookies.txt
```

## 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--urls` | URL 목록 텍스트 파일 | - |
| `--url` | 단일 URL | - |
| `--user` | TikTok 계정명 | - |
| `--hashtag` | 해시태그 | - |
| `--count` | 다운로드 최대 개수 | 100 |
| `--output` | 저장 폴더 | `downloads/` |
| `--cookies` | 쿠키 파일 (Netscape 형식) | - |

## 출력

- `downloads/` 폴더에 MP4 파일 저장
- `downloads/download_report.json` — 성공/실패 리포트
- `download.log` — 상세 로그

## 주의사항

- TikTok의 이용약관을 준수하세요.
- 개인적/학습 목적으로만 사용하세요.
- 과도한 요청은 IP 차단될 수 있습니다 (스크립트에 딜레이 내장).
