
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL_PATH = "kokoro-v1.0.int8.onnx"
VOICE_PATH = "voices-v1.0.bin"

print("Loading Kokoro on CPU...")
tts = Kokoro(MODEL_PATH, VOICE_PATH)

# Fix the speed input dtype for this ONNX model.
original_create_audio = tts._create_audio

def create_audio_fixed(phonemes, voice, speed):
    import numpy as np

    tokens = np.array(tts.tokenizer.tokenize(phonemes), dtype=np.int64)
    voice_style = voice[len(tokens)]
    tokens = [[0, *tokens, 0]]

    inputs = {
        "input_ids": tokens,
        "style": np.array(voice_style, dtype=np.float32),
        "speed": np.array([speed], dtype=np.float32),
    }

    audio = tts.sess.run(None, inputs)[0]
    return audio, 24000

tts._create_audio = create_audio_fixed

text = "Hello Qasim! I am AURA. I am speaking locally on your computer."

print("Generating speech...")
audio, sample_rate = tts.create(
    text,
    voice="af_sarah",
    speed=1.0,
    lang="en-us",
)

sf.write("kokoro_test.wav", audio, sample_rate)
print("Speech saved to kokoro_test.wav")
