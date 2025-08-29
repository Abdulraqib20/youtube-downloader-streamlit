# YouTube Downloader (yt-dlp)

A robust YouTube/video downloader script using yt-dlp.

## Setup

1) Install ffmpeg (recommended for merges, audio extraction, embedding):

- macOS (Homebrew):
  - `brew install ffmpeg`

2) Install Python deps:

- Create/activate your env (optional) and then:
  - `pip install -r requirements_ytdl.txt`

## Usage

Basic video:

- `python youtube_downloader.py https://www.youtube.com/watch?v=XXXX`

Batch file (one URL per line):

- `python youtube_downloader.py -a urls.txt -o ~/Videos`

Audio-only MP3 with embedded metadata and thumbnail:

- `python youtube_downloader.py -A mp3 --embed-metadata --embed-thumbnail https://youtu.be/XXXX`

Subtitles and playlist handling:

- `python youtube_downloader.py --subtitles --sub-langs en en-GB --yes-playlist PLAYLIST_URL`
- `python youtube_downloader.py --no-playlist https://www.youtube.com/watch?v=XXXX`

Advanced options:

- Cookies file for age-restricted/private videos: `--cookies cookies.txt`
- Proxy: `--proxy socks5://127.0.0.1:1080`
- Rate limit: `--rate-limit 1M`
- Archive to skip duplicates: `--download-archive downloaded.txt`
- Change output template: `-t "%(uploader)s/%(playlist_title)s/%(title)s [%(id)s].%(ext)s"`

Outputs default to `~/Downloads/yt-dlp`. Change with `-o`.

## Notes

- Ensure ffmpeg is on PATH for audio extraction, embedding subs/metadata/thumbnail, and merging best streams.
- Use responsibly. Download only content you have the rights or permission to download.

## Troubleshooting

- If `ffmpeg` is missing, install it and retry.
- If `yt_dlp` import error appears in editors, run `pip install -r requirements_ytdl.txt`.
- Some videos may be region-locked or require cookies; supply `--cookies` if needed.
