import os
import uuid
import requests
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
# SỬA Ở ĐÂY: MoviePy v2 không dùng .editor nữa
from moviepy import ImageClip, concatenate_videoclips

app = FastAPI()

# Thư mục tạm để xử lý
TEMP_DIR = "/tmp/video_processing"

def cleanup(folder_path: str):
    """Xóa toàn bộ file sau khi đã gửi video đi"""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

@app.post("/generate-video")
async def generate_video(data: dict, background_tasks: BackgroundTasks):
    image_urls = data.get("image_urls", [])
    duration = data.get("duration_per_image", 3)
    
    if not image_urls:
        raise HTTPException(status_code=400, detail="No images provided")

    project_id = str(uuid.uuid4())
    work_dir = os.path.join(TEMP_DIR, project_id)
    os.makedirs(work_dir, exist_ok=True)
    
    video_path = os.path.join(work_dir, "output.mp4")
    clips = []

    try:
        for i, url in enumerate(image_urls):
            img_path = os.path.join(work_dir, f"img_{i}.jpg")
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                # Cập nhật chuẩn MoviePy v2:
                # Dùng .with_duration thay cho .set_duration
                # Dùng .resized thay cho .resize
                clip = ImageClip(img_path).with_duration(duration)
                clip = clip.resized(height=720) 
                clips.append(clip)

        # Ghép video
        final_video = concatenate_videoclips(clips, method="compose")
        # Ghi file
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
