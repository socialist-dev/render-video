import os
import uuid
import shutil
from typing import List
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from moviepy import ImageClip, concatenate_videoclips

app = FastAPI()
TEMP_DIR = "/tmp/video_processing"

def cleanup(folder_path: str):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

@app.post("/generate-video-binary")
async def generate_video_binary(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    duration: int = 3
):
    project_id = str(uuid.uuid4())
    work_dir = os.path.join(TEMP_DIR, project_id)
    os.makedirs(work_dir, exist_ok=True)
    
    video_path = os.path.join(work_dir, "output.mp4")
    clips = []

    try:
        for i, file in enumerate(files):
            file_path = os.path.join(work_dir, f"img_{i}.jpg")
            # Lưu file binary trực tiếp từ n8n gửi sang
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            clip = ImageClip(file_path).with_duration(duration)
            clip = clip.resized(height=720) 
            clips.append(clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(video_path, fps=24, codec="libx264", audio=False)
        
        for c in clips:
            c.close()

        background_tasks.add_task(cleanup, work_dir)
        return FileResponse(video_path, media_type="video/mp4", filename="video.mp4")

    except Exception as e:
        cleanup(work_dir)
        return {"error": str(e)}

@app.get("/")
def health_check():
    return {"status": "ready"}
