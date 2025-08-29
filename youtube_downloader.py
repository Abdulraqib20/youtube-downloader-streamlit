#!/usr/bin/env python3
"""
YouTube downloader script built on yt-dlp.

Highlights:
- Single URL or batch file input
- Best quality video (merges best video + best audio) or audio-only extraction
- Subtitles download and embedding (requires ffmpeg)
- Playlists supported, resume, retries, download archive to skip duplicates
- Output filename template and directory control
- Cookies file and proxy support

Usage examples:
  python youtube_downloader.py https://www.youtube.com/watch?v=XXXX
  python youtube_downloader.py -a urls.txt -o ~/Videos
  python youtube_downloader.py -A mp3 https://youtu.be/XXXX --embed-metadata --embed-thumbnail

Note: Some features require ffmpeg installed and on PATH.
"""

from __future__ import annotations

import argparse
import os
import sys
import shutil
from typing import List, Optional
import yt_dlp


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def read_urls_from_file(path: str) -> List[str]:
    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="youtube_downloader",
        description="Download YouTube videos or audio reliably using yt-dlp.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Accept positional URLs and/or a batch file. We'll validate presence later.
    p.add_argument("urls", nargs="*", help="One or more video/playlist URLs.")
    p.add_argument(
        "-a",
        "--batch-file",
        dest="batch_file",
        help="Read URLs from a text file (one per line).",
    )

    p.add_argument(
        "-o",
        "--output-dir",
        default=os.path.join(os.getcwd(), "Downloads"),
        help="Directory to save downloads.",
    )

    p.add_argument(
        "-t",
        "--template",
        default="%(title)s [%(id)s].%(ext)s",
        help="Output filename template (yt-dlp outtmpl syntax).",
    )

    p.add_argument(
        "-f",
        "--format",
        default="bestvideo*+bestaudio/best",
        help="Format selection. For video downloads.",
    )

    p.add_argument(
        "-m",
        "--merge-format",
        dest="merge_format",
        default="mp4",
        choices=["mp4", "mkv", "webm"],
        help="Container used when merging bestvideo+bestaudio.",
    )

    p.add_argument(
        "-A",
        "--audio-only",
        dest="audio_format",
        choices=["mp3", "m4a", "opus", "wav", "flac", "aac"],
        help="Download audio only and convert to this format.",
    )

    p.add_argument(
        "--audio-quality",
        default="0",
        help="FFmpeg audio quality. For mp3 0=best, 9=worst.",
    )

    p.add_argument(
        "--subtitles",
        action="store_true",
        help="Download subtitles if available.",
    )
    p.add_argument(
        "--sub-langs",
        nargs="+",
        default=["en"],
        help="Subtitle language codes (e.g., en, en-US).",
    )
    p.add_argument(
        "--auto-subs",
        action="store_true",
        help="Allow auto-generated subtitles if normal subs are unavailable.",
    )

    p.add_argument(
        "--embed-metadata",
        action="store_true",
        help="Embed metadata into media file (requires ffmpeg).",
    )
    p.add_argument(
        "--embed-thumbnail",
        action="store_true",
        help="Embed thumbnail into media file (requires ffmpeg).",
    )
    p.add_argument(
        "--embed-subs",
        action="store_true",
        help="Embed subtitles where possible (requires ffmpeg).",
    )
    p.add_argument(
        "--write-thumbnail",
        action="store_true",
        help="Download thumbnail image alongside media.",
    )

    p.add_argument(
        "--cookies",
        help="Path to a cookies.txt file for authenticated/age-restricted videos.",
    )
    p.add_argument(
        "--proxy",
        help="HTTP/HTTPS/SOCKS proxy URL (e.g., socks5://127.0.0.1:1080).",
    )
    p.add_argument(
        "--rate-limit",
        help="Maximum download rate (e.g., 1M or 500K).",
    )
    p.add_argument(
        "--retries",
        default=10,
        type=int,
        help="Number of retries for network errors.",
    )
    p.add_argument(
        "--fragment-retries",
        default=10,
        type=int,
        help="Retries per fragment for HLS/DASH downloads.",
    )
    p.add_argument(
        "--concurrent-fragments",
        type=int,
        default=5,
        help="Number of fragments to download concurrently.",
    )
    p.add_argument(
        "--no-check-certificate",
        action="store_true",
        help="Disable SSL certificate verification (not recommended).",
    )
    p.add_argument(
        "--download-archive",
        help="Path to an archive file to record downloaded video IDs (skips duplicates).",
    )
    p.add_argument(
        "--no-playlist",
        action="store_true",
        help="Download only the video, if a playlist URL is given.",
    )
    p.add_argument(
        "--yes-playlist",
        action="store_true",
        help="Process full playlist if URL is a playlist.",
    )

    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less verbose output.",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="More verbose output (overrides quiet).",
    )

    return p


def make_ydl_opts(args: argparse.Namespace) -> dict:
    outdir = os.path.abspath(os.path.expanduser(args.output_dir))
    os.makedirs(outdir, exist_ok=True)

    outtmpl = os.path.join(outdir, args.template)

    ydl_opts: dict = {
        "outtmpl": outtmpl,
        "ignoreerrors": True,  # continue on download errors
        "noplaylist": args.no_playlist and not args.yes_playlist,
        "skip_unavailable_fragments": True,
        "retries": args.retries,
        "fragment_retries": args.fragment_retries,
        "concurrent_fragment_downloads": args.concurrent_fragments,
        "continuedl": True,
        "merge_output_format": args.merge_format,
    }

    if args.verbose:
        ydl_opts["verbose"] = True
    elif args.quiet:
        ydl_opts["quiet"] = True

    if args.rate_limit:
        ydl_opts["ratelimit"] = args.rate_limit

    if args.cookies:
        ydl_opts["cookiefile"] = args.cookies

    if args.proxy:
        ydl_opts["proxy"] = args.proxy

    if args.download_archive:
        ydl_opts["download_archive"] = args.download_archive

    if args.no_check_certificate:
        ydl_opts["nocheckcertificate"] = True

    # Subtitles
    if args.subtitles:
        ydl_opts["writesubtitles"] = True
        ydl_opts["subtitleslangs"] = args.sub_langs
        if args.auto_subs:
            ydl_opts["writeautomaticsub"] = True
    if args.embed_subs:
        ydl_opts["embedsubtitles"] = True

    # Thumbnails and metadata
    if args.write_thumbnail:
        ydl_opts["writethumbnail"] = True
    if args.embed_thumbnail:
        ydl_opts["embedthumbnail"] = True
    if args.embed_metadata:
        ydl_opts["addmetadata"] = True

    # Audio-only mode via postprocessor
    if args.audio_format:
        # Force bestaudio for download format
        ydl_opts["format"] = "bestaudio/best"
        pp = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": args.audio_format,
            "preferredquality": args.audio_quality,
        }
        ydl_opts.setdefault("postprocessors", []).append(pp)
        # For embedding thumbnail/metadata in audio containers
        if args.embed_thumbnail:
            ydl_opts.setdefault("postprocessors", []).append({"key": "FFmpegThumbnailsConvertor", "format": "jpg"})
    else:
        # Video mode
        ydl_opts["format"] = args.format

    # Warn about ffmpeg-dependent features
    if (args.embed_metadata or args.embed_thumbnail or args.embed_subs or args.audio_format) and not ffmpeg_available():
        print(
            "Warning: ffmpeg not found on PATH. Embedding/convert features may be disabled.",
            file=sys.stderr,
        )

    return ydl_opts


def collect_urls(args: argparse.Namespace) -> List[str]:
    urls: List[str] = []
    if args.batch_file:
        urls.extend(read_urls_from_file(args.batch_file))
    if args.urls:
        urls.extend(args.urls)
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def download(urls: List[str], ydl_opts: dict) -> int:
    if not urls:
        print("No URLs to download.", file=sys.stderr)
        return 2
    # Use yt-dlp with progress and error handling
    exit_codes: List[int] = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            code = ydl.download(urls)
            if isinstance(code, int):
                exit_codes.append(code)
        except yt_dlp.utils.DownloadError:
            # yt-dlp already logs errors; use non-zero exit
            exit_codes.append(1)
        except Exception as e:  # pragma: no cover
            print(f"Unexpected error: {e}", file=sys.stderr)
            exit_codes.append(1)

    return 0 if all(c == 0 for c in exit_codes) else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    urls = collect_urls(args)
    if not urls:
        print("Error: No URLs provided after processing inputs.", file=sys.stderr)
        return 2

    ydl_opts = make_ydl_opts(args)
    return download(urls, ydl_opts)


if __name__ == "__main__":
    sys.exit(main())
