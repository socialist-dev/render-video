import os
import uuid
import shutil
from typing import List
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from moviepy import ImageClip, concatenate_videoclips

app = FastAPI()
# Sử dụng /tmp là thư mục lưu trữ tạm thời trên Render
TEMP_DIR = "/tmp/video_processing"

def cleanup(folder_path: str):
    """Xóa dữ liệu sau khi xử lý để giải phóng bộ nhớ"""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Dọn dẹp thành công: {folder_path}")

@app.post("/generate-video-binary")
async def generate_video_binary(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    duration: int = 3
):
    # Tạo định danh duy nhất cho mỗi yêu cầu để không bị lẫn dữ liệu
    project_id = str(uuid.uuid4())
    work_dir = os.path.join(TEMP_DIR, project_id)
    os.makedirs(work_dir, exist_ok=True)
    
    video_path = os.path.join(work_dir, "output.mp4")
    clips = []

    try:
        for i, file in enumerate(files):
            file_path = os.path.join(work_dir, f"img_{i}.jpg")
            # Lưu file binary từ n8n vào ổ cứng tạm
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # CẤU HÌNH CHẤT LƯỢNG TẠI ĐÂY:
            # .resized(height=1080) -> Nâng cấp lên Full HD
            clip = ImageClip(file_path).with_duration(duration)
            clip = clip.resized(height=1080) 
            clips.append(clip)

        # Ghép các đoạn ảnh lại thành video
        final_video = concatenate_videoclips(clips, method="compose")
        
        # XUẤT FILE VỚI ĐỘ SẮC NÉT CAO (Bitrate 5000k)
        final_video.write_videofile(
            video_path, 
            fps=24, 
            codec="libx264", 
            audio=False,
            bitrate="5000k",
            threads=2,      # Giới hạn luồng để tránh quá tải CPU Render Free
            preset="fast"   # Tốc độ xử lý nhanh để tránh bị Timeout
        )
        
        # Đóng các clip để giải phóng RAM ngay lập tức
        for c in clips:
            c.close()
        final_video.close()

        # Sau khi gửi file xong, n8n nhận được thì Render sẽ tự chạy lệnh xóa này
        background_tasks.add_task(cleanup, work_dir)
        
        return FileResponse(
            video_path, 
            media_type="video/mp4", 
            filename="video_fullhd.mp4"
        )

    except Exception as e:
        cleanup(work_dir)
        return {"error": str(e)}

@app.get("/")
def health_check():
    return {"status": "ready", "resolution": "1080p", "bitrate": "5000k"}
