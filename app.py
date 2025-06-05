import streamlit as st
import cv2
import tempfile
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips

st.set_page_config(page_title="Smart Video Trimmer", layout="centered")
st.title("🎬 Smart Video Trimmer (No Scene Detection)")

uploaded_file = st.file_uploader("Upload a video (up to 1GB)", type=["mp4", "mov"], accept_multiple_files=False, key="video_uploader", help="Max file size: 1GB")

st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    st.video(video_path)
    st.info("⏳ Trimming video into segments... Please wait.")

    clip = VideoFileClip(video_path)
    duration = int(clip.duration)

    if duration < 180:
        st.warning("⚠️ Short video detected. Will generate shorter clips.")
        segment_length = max(10, duration // 3)  # minimum 10 seconds
        starts = [i * segment_length for i in range(duration // segment_length)]
        selected_segments = [(start, min(start + segment_length, duration)) for start in starts[:3]]
    else:
        segment_length = 60
        spacing = (duration - segment_length * 3) // 4
        starts = [spacing, spacing * 2 + segment_length, spacing * 3 + segment_length * 2]
        selected_segments = [(start, start + segment_length) for start in starts if start + segment_length <= duration]

    merged_clips = []
    for start, end in selected_segments:
        try:
            subclip = clip.subclip(start, end)
            merged_clips.append(subclip)
        except Exception as e:
            st.warning(f"⚠️ Skipped a segment due to error: {e}")

    if merged_clips:
        final_clip = concatenate_videoclips(merged_clips)
        merged_path = os.path.join(tempfile.gettempdir(), "merged_summary_clip.mp4")
        final_clip.write_videofile(merged_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.video(merged_path)
        with open(merged_path, "rb") as f:
            st.download_button(
                label="📥 Download Trimmed Summary",
                data=f.read(),
                file_name="summary_clip.mp4",
                mime="video/mp4"
            )
    else:
        st.error("❌ No clips were successfully created.")
