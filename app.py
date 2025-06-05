import streamlit as st
import cv2
import tempfile
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

st.set_page_config(page_title="Scene-Based Video Trimmer", layout="centered")
st.title("🎬 Scene-Based Video Trimmer")

uploaded_file = st.file_uploader("Upload a video (up to 1GB)", type=["mp4", "mov"], accept_multiple_files=False, key="video_uploader", help="Max file size: 1GB")

st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    st.video(video_path)
    st.info("⏳ Detecting scenes and trimming... Please wait.")

    # Scene detection setup
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30.0))

    try:
        video_manager.set_downscale_factor()
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
    finally:
        video_manager.release()

    if len(scene_list) < 3:
        st.error("❌ Not enough distinct scenes found. Try a longer or more dynamic video.")
        st.stop()

    # Convert scene timecodes to seconds
    scene_times = [(scene[0].get_seconds(), scene[1].get_seconds()) for scene in scene_list]
    scene_times = sorted(scene_times, key=lambda x: x[1] - x[0], reverse=True)[:3]  # pick 3 longest scenes

    merged_clips = []
    clip = VideoFileClip(video_path)
    for start, end in scene_times:
        try:
            subclip = clip.subclip(start, end)
            merged_clips.append(subclip)
        except Exception as e:
            st.warning(f"⚠️ Skipped a scene due to error: {e}")

    if merged_clips:
        final_clip = concatenate_videoclips(merged_clips)
        merged_path = os.path.join(tempfile.gettempdir(), "merged_scene_clip.mp4")
        final_clip.write_videofile(merged_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        st.video(merged_path)
        with open(merged_path, "rb") as f:
            st.download_button(
                label="📥 Download Scene Summary",
                data=f.read(),
                file_name="scene_summary.mp4",
                mime="video/mp4"
            )
    else:
        st.error("❌ No clips were successfully created from detected scenes.")
