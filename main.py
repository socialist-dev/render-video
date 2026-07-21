import os
import uuid
import requests
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from moviepy.editor import ImageClip, concatenate_videoclips

app = FastAPI()

# Thư mục tạm để xử lý
TEMP_DIR = "/tmp/video_processing"

def cleanup(folder_path: str):
    """Xóa toàn bộ file sau khi đã gửi video đi để giải phóng bộ nhớ"""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Cleaned up: {folder_path}")

@app.post("/generate-video")
async def generate_video(data: dict, background_tasks: BackgroundTasks):
    # Dữ liệu mong đợi: {"image_urls": ["url1", "url2"], "fps": 24, "duration_per_image": 3}
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
            # Tải ảnh từ Google Drive (n8n gửi link trực tiếp)
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                # Tạo clip từ ảnh, resize để tiết kiệm RAM (Quan trọng!)
                clip = ImageClip(img_path).set_duration(duration)
                clip = clip.resize(height=720) # Giới hạn 720p để ko tràn RAM
                clips.append(clip)

        # Ghép video
        final_video = concatenate_videoclips(clips, method="compose")
        # Ghi file với bitrate thấp để xử lý nhanh và nhẹ
        final_video.write_videofile(video_path, fps=24, codec="libx264", audio=False)
        
        # Đóng các clip để giải phóng RAM ngay lập tức
        for c in clips:
            c.close()

        # Lên lịch xóa file sau khi phản hồi được gửi đi
        background_tasks.add_task(cleanup, work_dir)

        return FileResponse(video_path, media_type="video/mp4", filename="video.mp4")

    except Exception as e:
        cleanup(work_dir)
        return {"error": str(e)}

@app.get("/")
def health_check():
    return {"status": "ready"}