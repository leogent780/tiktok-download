#!/usr/bin/env python3
"""
TikTok 바이럴 영상 자동 다운로더

사용법:
  # URL 목록 파일로 다운로드
  python3 downloader.py --urls urls.txt --count 100

  # 해시태그 기반 다운로드
  python3 downloader.py --hashtag funny --count 100

  # 특정 계정 영상 다운로드
  python3 downloader.py --user username --count 100

  # 직접 URL 입력
  python3 downloader.py --url https://www.tiktok.com/@user/video/123456
"""

import argparse
import os
import sys
import time
import json
import logging
from pathlib import Path

import yt_dlp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("download.log"),
    ],
)
log = logging.getLogger(__name__)


def make_ydl_opts(output_dir: str, cookies_file: str | None = None) -> dict:
    opts = {
        "outtmpl": os.path.join(output_dir, "%(uploader)s_%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "sleep_interval": 2,
        "max_sleep_interval": 5,
        "writeinfojson": True,  # 메타데이터 저장
        "writethumbnail": True,  # 썸네일 저장
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
    }
    if cookies_file and Path(cookies_file).exists():
        opts["cookiefile"] = cookies_file
    return opts


def download_from_url_list(urls: list[str], output_dir: str, cookies_file: str | None = None) -> dict:
    """URL 목록에서 영상 다운로드"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = {"success": [], "failed": []}

    for i, url in enumerate(urls, 1):
        url = url.strip()
        if not url or url.startswith("#"):
            continue
        log.info(f"[{i}/{len(urls)}] 다운로드 중: {url}")
        try:
            with yt_dlp.YoutubeDL(make_ydl_opts(output_dir, cookies_file)) as ydl:
                ydl.download([url])
            results["success"].append(url)
            log.info(f"  완료: {url}")
        except yt_dlp.utils.DownloadError as e:
            log.warning(f"  실패: {url} — {e}")
            results["failed"].append({"url": url, "error": str(e)})
        time.sleep(2)  # 요청 간 딜레이 (차단 방지)

    return results


def download_from_user(username: str, count: int, output_dir: str, cookies_file: str | None = None) -> dict:
    """특정 TikTok 계정의 영상 다운로드"""
    url = f"https://www.tiktok.com/@{username}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    opts = make_ydl_opts(output_dir, cookies_file)
    opts["playlistend"] = count

    log.info(f"계정 @{username} 에서 최대 {count}개 다운로드 시작")
    results = {"success": [], "failed": []}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        results["success"].append(username)
    except yt_dlp.utils.DownloadError as e:
        log.error(f"다운로드 실패: {e}")
        results["failed"].append({"url": url, "error": str(e)})

    return results


def download_from_hashtag(hashtag: str, count: int, output_dir: str, cookies_file: str | None = None) -> dict:
    """해시태그 기반 영상 다운로드"""
    hashtag = hashtag.lstrip("#")
    url = f"https://www.tiktok.com/tag/{hashtag}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    opts = make_ydl_opts(output_dir, cookies_file)
    opts["playlistend"] = count

    log.info(f"해시태그 #{hashtag} 에서 최대 {count}개 다운로드 시작")
    results = {"success": [], "failed": []}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        results["success"].append(hashtag)
    except yt_dlp.utils.DownloadError as e:
        log.error(f"다운로드 실패: {e}")
        results["failed"].append({"url": url, "error": str(e)})

    return results


def save_results(results: dict, output_dir: str):
    report_path = os.path.join(output_dir, "download_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log.info(f"결과 리포트 저장: {report_path}")
    log.info(f"성공: {len(results.get('success', []))}개 / 실패: {len(results.get('failed', []))}개")


def main():
    parser = argparse.ArgumentParser(description="TikTok 바이럴 영상 자동 다운로더")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--urls", help="URL 목록 텍스트 파일 경로 (한 줄에 URL 하나)")
    source.add_argument("--url", help="단일 TikTok URL")
    source.add_argument("--user", help="TikTok 계정 이름 (@ 제외)")
    source.add_argument("--hashtag", help="다운로드할 해시태그 (# 제외)")

    parser.add_argument("--count", type=int, default=100, help="다운로드할 최대 영상 수 (기본값: 100)")
    parser.add_argument("--output", default="downloads", help="저장 폴더 (기본값: downloads)")
    parser.add_argument("--cookies", default=None, help="쿠키 파일 경로 (Netscape 형식, 로그인 필요 시)")

    args = parser.parse_args()

    if args.urls:
        with open(args.urls, encoding="utf-8") as f:
            urls = f.readlines()
        urls = [u.strip() for u in urls if u.strip() and not u.startswith("#")]
        urls = urls[: args.count]
        results = download_from_url_list(urls, args.output, args.cookies)

    elif args.url:
        results = download_from_url_list([args.url], args.output, args.cookies)

    elif args.user:
        results = download_from_user(args.user, args.count, args.output, args.cookies)

    elif args.hashtag:
        results = download_from_hashtag(args.hashtag, args.count, args.output, args.cookies)

    save_results(results, args.output)


if __name__ == "__main__":
    main()
