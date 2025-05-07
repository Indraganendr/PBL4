import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.utils import which
import tempfile
import io
import os
import simpleaudio

# Pastikan pydub tahu lokasi ffmpeg dan ffprobe
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe   = which("ffprobe")

client = ElevenLabs(api_key="ELEVEN_API_KEY")

recognizer = sr.Recognizer()    
mic = sr.Microphone()

print("🎤 Silakan bicara (ucapkan 'exit' untuk keluar)")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🕒 Mendengarkan...")
        audio = recognizer.listen(source)

    try:
        user_text = recognizer.recognize_google(audio, language="id-ID")
        print(f"👤 Kamu: {user_text}")

        if user_text.lower() in ["exit", "keluar", "berhenti"]:
            print("👋 Sampai jumpa!")
            break

        response = f"Kamu bilang: {user_text}"

        audio_stream = client.generate(
            text=response,
            voice="Rachel",
            model="eleven_monolingual_v1"
        )

        full_audio = b''.join(audio_stream)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(full_audio)
            temp_audio_path = temp_audio.name

        sound = AudioSegment.from_file(temp_audio_path, format="mp3")

        play_obj = simpleaudio.play_buffer(
            sound.raw_data,
            num_channels=sound.channels,
            bytes_per_sample=sound.sample_width,
            sample_rate=sound.frame_rate
        )
        play_obj.wait_done()

        os.remove(temp_audio_path)

    except sr.UnknownValueError:
        print("❌ Maaf, saya tidak bisa memahami.")
    except sr.RequestError as e:
        print(f"⚠️ Google Speech API error: {e}")
    except Exception as e:
        print(f"⚠️ Error lain: {e}")
