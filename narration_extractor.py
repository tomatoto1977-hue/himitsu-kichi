import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class SceneScript(BaseModel):
    scene_index: int = Field(..., description="シーン番号")
    visual_description: str = Field(..., description="画面指示")
    narration_text: str = Field(..., description="読み上げ音声テキスト")

    @field_validator('narration_text')
    @classmethod
    def sanitize_narration(cls, v: str) -> str:
        cleaned = re.sub(r"\[.*?\]|【.*?】", "", v)
        cleaned = re.sub(r"(SCENE|シーン)\s*\d+[:：]?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(タイトル|ナレーション|演出|画面|BGM|SFX)[:：]", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

class NarrationExtractor:
    @classmethod
    def process_scenes(cls, raw_scenes: List[Dict[str, Any]]) -> List[SceneScript]:
        validated = []
        for idx, scene in enumerate(raw_scenes, start=1):
            raw_text = scene.get("narration_text", "")
            script = SceneScript(
                scene_index=idx,
                visual_description=scene.get("visual_description", ""),
                narration_text=raw_text
            )
            validated.append(script)
        return validated
