# processor.py
import os
import subprocess
import yt_dlp
import whisper
from transformers import pipeline
import datetime


# -------------------------------------------------------
# 1) DOWNLOAD AUDIO FROM YOUTUBE
# -------------------------------------------------------
def download_audio(url, output="audio.webm"):
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": output,
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output


# -------------------------------------------------------
# 2) CONVERT TO WAV USING FFMPEG
# -------------------------------------------------------
def convert_to_wav(inp, out="audio.wav"):
    cmd = [
        "ffmpeg", "-y",
        "-i", inp,
        "-ac", "1",
        "-ar", "16000",
        out
    ]
    subprocess.run(cmd, check=True)
    return out


# -------------------------------------------------------
# 3) FULL TRANSCRIPTION USING WHISPER (tiny = fast)
# -------------------------------------------------------
def transcribe_audio(wav):
    model = whisper.load_model("tiny")
    result = model.transcribe(wav, verbose=False)
    return result["text"]


# -------------------------------------------------------
# 4) SUMMARIZATION
# -------------------------------------------------------
def summarize_text(text):
    summarizer = pipeline("summarization", model="google/pegasus-xsum")
    chunks = []
    size = 900

    for i in range(0, len(text), size):
        piece = text[i:i+size]
        sum_text = summarizer(piece)[0]["summary_text"]
        chunks.append(sum_text)

    return " ".join(chunks)


# -------------------------------------------------------
# 5) BULLET POINTS
# -------------------------------------------------------
def make_bullets(summary):
    lines = summary.split(". ")
    bullets = ["• " + line.strip() for line in lines if len(line.strip()) > 3]
    return "\n".join(bullets)


# -------------------------------------------------------
# 6) TIMESTAMPS (simple — every 1 minute)
# -------------------------------------------------------
def make_timestamps(transcript, interval=60):
    words = transcript.split()
    wpm = 150  # rough estimate
    chunk_size = int(wpm * (interval / 60))

    timestamps = []
    for i in range(0, len(words), chunk_size):
        ts = str(datetime.timedelta(seconds=(i // chunk_size) * interval))
        text = " ".join(words[i:i+chunk_size])
        timestamps.append(f"[{ts}] {text}")

    return timestamps


# -------------------------------------------------------
# 7) CHAPTERS (simple — every 5 mins)
# -------------------------------------------------------
def make_chapters(transcript, interval=300):
    words = transcript.split()
    wpm = 150
    chunk_size = int(wpm * (interval / 60))

    chapters = []
    for i in range(0, len(words), chunk_size):
        ts = str(datetime.timedelta(seconds=(i // chunk_size) * interval))
        preview = (" ".join(words[i:i+40])) + "..."
        chapters.append(f"Chapter at {ts} — {preview}")

    return chapters


# -------------------------------------------------------
# 8) MAIN PROCESSOR
#  ⭐ FIX ADDED → DELETE OLD AUDIO FILES ⭐
# -------------------------------------------------------
def process_youtube(url, workdir="."):

    os.makedirs(workdir, exist_ok=True)

    # Always remove old audio — FIX FOR YOUR ISSUE
    old_files = ["audio.webm", "audio.wav"]
    for file in old_files:
        path = os.path.join(workdir, file)
        if os.path.exists(path):
            os.remove(path)

    webm = os.path.join(workdir, "audio.webm")
    wav = os.path.join(workdir, "audio.wav")

    download_audio(url, webm)
    convert_to_wav(webm, wav)

    transcript = transcribe_audio(wav)
    summary = summarize_text(transcript)

    bullets = make_bullets(summary)
    timestamps = make_timestamps(transcript)
    chapters = make_chapters(transcript)

    # Save summary file
    with open(os.path.join(workdir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary)

    return {
        "transcript": transcript,
        "summary": summary,
        "bullets": bullets,
        "timestamps": timestamps,
        "chapters": chapters,
    }
