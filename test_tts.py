
import os
import winsound
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

output_path = Path("aura_tts_test.wav")

print("Requesting speech from Groq...")

response = client.audio.speech.create(
    model="canopylabs/orpheus-v1-english",
    voice="troy",
    input="Hello Qasim. AURA is testing its voice output.",
    response_format="wav",
)

response.write_to_file(str(output_path))

print(f"Audio saved: {output_path.resolve()}")
print(f"Audio size: {output_path.stat().st_size} bytes")
print("Playing audio now...")

winsound.PlaySound(
    str(output_path.resolve()),
    winsound.SND_FILENAME,
)

print("Playback finished.")
