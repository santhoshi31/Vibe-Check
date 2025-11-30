import os
import subprocess
import yt_dlp
import whisper
from transformers import pipeline
from fpdf import FPDF
from processor import process_youtube
import sys


# -------------------------------------------------------
# 1) DOWNLOAD YOUTUBE AUDIO
# -------------------------------------------------------

def download_audio(url, output="audio.webm"):
    print("Downloading audio using yt-dlp...")

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": output,
        "quiet": False,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("Downloaded:", output)
    return output


# -------------------------------------------------------
# 2) CONVERT TO WAV
# -------------------------------------------------------

def convert_to_wav(input_path, output_path="audio.wav"):
    print("Converting to WAV...")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path
    ]

    subprocess.run(cmd, check=True)
    return output_path


# -------------------------------------------------------
# 3) TRANSCRIBE WITH TIMESTAMPS
# -------------------------------------------------------

def transcribe_audio(wav_file):
    print("Loading Whisper model (medium)...")
    model = whisper.load_model("medium")

    print("Transcribing with timestamps...")
    result = model.transcribe(wav_file, verbose=False)

    text = result["text"]
    segments = result["segments"]  # timestamps available here

    return text, segments


# -------------------------------------------------------
# 4) GENERATE CHAPTERS
# -------------------------------------------------------

def create_chapters(segments):
    chapters = []
    chapter_size = 120  # seconds per chapter

    current = []
    start = segments[0]["start"]

    for seg in segments:
        current.append(seg["text"])

        if seg["end"] - start >= chapter_size:
            chapters.append({
                "start": start,
                "end": seg["end"],
                "text": " ".join(current)
            })
            current = []
            start = seg["end"]

    # Add last chapter
    if current:
        chapters.append({
            "start": start,
            "end": segments[-1]["end"],
            "text": " ".join(current)
        })

    return chapters


# -------------------------------------------------------
# 5) SUMMARIZE (PEGASUS)
# -------------------------------------------------------

def summarize_text(text):
    print("\nSummarizing...")
    summarizer = pipeline("summarization", model="google/pegasus-xsum")

    chunks = []
    size = 800

    for i in range(0, len(text), size):
        chunk = text[i:i + size]
        out = summarizer(chunk)[0]["summary_text"]
        chunks.append(out)

    return " ".join(chunks)


# -------------------------------------------------------
# 6) FORMAT OUTPUT (pretty text)
# -------------------------------------------------------

def format_output(summary, chapters, segments):
    final_text = ""

    final_text += "===== FINAL SUMMARY =====\n"
    final_text += summary + "\n\n"

    final_text += "===== CHAPTERS =====\n"
    for i, c in enumerate(chapters):
        final_text += f"\n--- Chapter {i+1} ({int(c['start'])}s → {int(c['end'])}s) ---\n"
        final_text += c["text"] + "\n"

    final_text += "\n===== TIMESTAMPS =====\n"
    for seg in segments:
        final_text += f"{int(seg['start'])}s → {int(seg['end'])}s : {seg['text']}\n"

    final_text += "\n===== BULLET POINT SUMMARY =====\n"
    for line in summary.split("."):
        if len(line.strip()) > 5:
            final_text += "• " + line.strip() + ".\n"

    return final_text


# -------------------------------------------------------
# 7) EXPORT PDF
# -------------------------------------------------------

def save_pdf(text, filename="summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 10)
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)
    print("Saved:", filename)


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")

    webm = download_audio(url)
    wav = convert_to_wav(webm)

    transcript, segments = transcribe_audio(wav)

    chapters = create_chapters(segments)

    summary = summarize_text(transcript)

    formatted = format_output(summary, chapters, segments)

    # Save text file
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(formatted)

    print("\nSaved summary.txt")

    # Save PDF
    save_pdf(formatted)

    print("\nAll tasks completed successfully!")
