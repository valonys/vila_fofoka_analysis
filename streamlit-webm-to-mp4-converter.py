import streamlit as st
import os
import tempfile
from moviepy.editor import VideoFileClip

def convert_webm_to_mp4(input_file):
    # Create a temporary directory to store the converted file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate output filename
        output_filename = os.path.splitext(os.path.basename(input_file.name))[0] + ".mp4"
        output_path = os.path.join(temp_dir, output_filename)

        # Convert WebM to MP4
        video = VideoFileClip(input_file.name)
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Read the converted file
        with open(output_path, "rb") as file:
            converted_file = file.read()

    return output_filename, converted_file

def main():
    st.title("WebM to MP4 Converter")

    # Sidebar for file upload
    st.sidebar.header("Upload WebM File")
    uploaded_file = st.sidebar.file_uploader("Choose a WebM file", type=["webm"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # Convert the file
        with st.spinner("Converting WebM to MP4..."):
            output_filename, converted_file = convert_webm_to_mp4(temp_file)

        # Remove the temporary file
        os.unlink(temp_file_path)

        # Display download button for the converted file
        st.success("Conversion completed!")
        st.download_button(
            label="Download MP4",
            data=converted_file,
            file_name=output_filename,
            mime="video/mp4"
        )

        # Display video player
        st.video(converted_file)

    else:
        st.info("Please upload a WebM file using the sidebar.")

if __name__ == "__main__":
    main()
