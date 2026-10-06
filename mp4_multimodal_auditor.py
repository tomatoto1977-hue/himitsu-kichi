import os
import time
import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

class GeminiVideoAuditor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))

    def audit_mp4_file(self, video_path: str) -> Dict[str, Any]:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが存在しません: {video_path}")

        video_file = self.client.files.upload(file=video_path)
        while video_file.state.name == "PROCESSING":
            time.sleep(4)
            video_file = self.client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            raise RuntimeError(f"動画解析失敗: {video_file.error.message}")

        prompt = """
あなたは短尺動画の品質監査官です。アップロードされた動画の映像・音声を全編評価し、以下のJSON形式で出力してください。
{
  "overall_verdict": "PASS" または "NEEDS_REVIEW",
  "audit_score": 0〜100の数値,
  "item_evaluations": {
    "first_2sec_hook": {"pass": true/false, "comment": "理由"},
    "scene_pacing": {"pass": true/false, "comment": "理由"},
    "caption_readability": {"pass": true/false, "comment": "理由"},
    "audio_balance": {"pass": true/false, "comment": "理由"},
    "no_label_leak": {"pass": true/false, "comment": "理由"}
  },
  "detected_issues": ["問題点"],
  "improvement_suggestions": ["改善点"]
}
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[video_file, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            self.client.files.delete(name=video_file.name)
            return json.loads(response.text)
        except Exception as e:
            try:
                self.client.files.delete(name=video_file.name)
            except:
                pass
            raise e
