import os
import time
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types

from narration_extractor import NarrationExtractor
from mp4_multimodal_auditor import GeminiVideoAuditor
from video_builder import VideoBuilder

app = FastAPI(title="秘密基地 API", version="1.0.0")

class PipelineRequest(BaseModel):
    theme: str

@app.get("/")
def health_check():
    return {"status": "online", "system": "秘密基地 最適版 Engine"}

@app.post("/api/v1/generate-full-pipeline")
def generate_full_pipeline(req: PipelineRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 未設定")

    client = genai.Client(api_key=api_key)

    # 1. Geminiで台本生成
    prompt = f"テーマ「{req.theme}」でSNS短尺動画(12シーン)の台本をJSON生成してください。キーは scene_index, visual_description, narration_text。"
    res = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    raw_scenes = json.loads(res.text)

    # 2. ナレーションサニタイズ
    cleaned_scenes = NarrationExtractor.process_scenes(raw_scenes)

    # 3. MP4動画生成
    builder = VideoBuilder()
    filename = f"video_{int(time.time())}.mp4"
    mp4_path = builder.build_video(cleaned_scenes, filename=filename)

    # 4. Gemini実物マルチモーダル監査
    auditor = GeminiVideoAuditor(api_key=api_key)
    audit_report = auditor.audit_mp4_file(mp4_path)

    return {
        "status": "success",
        "theme": req.theme,
        "generated_video_path": mp4_path,
        "audit_report": audit_report
    }
