import streamlit as st
from processor import process_youtube

st.set_page_config(page_title="AI Video Summarizer", layout="wide")

st.title("🎬 AI YouTube Video Summarizer")
st.write("Paste a YouTube URL below and get transcript + summary.")

url = st.text_input("YouTube URL", "")

if st.button("Generate Summary"):
    if url.strip() == "":
        st.error("Please enter a valid YouTube link.")
    else:
        with st.spinner("Processing... This may take a few minutes ⏳"):
            result = process_youtube(url)

        st.success("Done! 🎉")

        st.subheader("📄 Summary")
        st.write(result["summary"])

        st.subheader("📝 Transcript")
        st.write(result["transcript"])

        # save files
        with open("summary.txt", "w", encoding="utf-8") as f:
            f.write(result["summary"])

        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(result["transcript"])

        st.download_button("⬇️ Download Summary", data=result["summary"], file_name="summary.txt")
        st.download_button("⬇️ Download Transcript", data=result["transcript"], file_name="transcript.txt")
