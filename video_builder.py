import os
import tempfile
from typing import List
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
from narration_extractor import SceneScript

class VideoBuilder:
    def __init__(self, output_dir: str = "output_videos"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def render_scene(self, scene: SceneScript, temp_dir: str) -> CompositeVideoClip:
        audio_path = os.path.join(temp_dir, f"scene_{scene.scene_index}.mp3")
        tts = gTTS(text=scene.narration_text, lang='ja')
        tts.save(audio_path)
        
        audio_clip = AudioFileClip(audio_path)
        duration = max(audio_clip.duration, 3.0)

        bg_color = (15, 23, 42) if scene.scene_index % 2 == 1 else (30, 41, 59)
        bg_clip = ColorClip(size=(1080, 1920), color=bg_color, duration=duration)

        txt_clip = TextClip(
            scene.narration_text, fontsize=48, color='white',
            font='Arial-Bold', size=(900, None), method='caption'
        ).set_position(('center', 1300)).set_duration(duration)

        header_clip = TextClip(
            f"SCENE {scene.scene_index}", fontsize=36, color='yellow', font='Arial-Bold'
        ).set_position(('center', 200)).set_duration(duration)

        return CompositeVideoClip([bg_clip, txt_clip, header_clip]).set_audio(audio_clip)

    def build_video(self, scenes: List[SceneScript], filename: str = "generated_short.mp4") -> str:
        output_path = os.path.join(self.output_dir, filename)
        with tempfile.TemporaryDirectory() as temp_dir:
            scene_clips = [self.render_scene(s, temp_dir) for s in scenes]
            final_clip = concatenate_videoclips(scene_clips, method="compose")
            final_clip.write_videofile(
                output_path, fps=24, codec="libx264", audio_codec="aac",
                temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"), remove_temp=True
            )
            for clip in scene_clips:
                clip.close()
            final_clip.close()
        return output_path
