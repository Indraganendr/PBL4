import os
import io
import tempfile
import speech_recognition as sr
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.utils import which
import simpleaudio

# Konfigurasi FFMPEG
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")


# Konfigurasi Gemini
genai.configure(api_key="GEMINI_API_KEY")
gemini_model = genai.GenerativeModel("gemini-1.5-pro")

# Konfigurasi ElevenLabs
eleven_client = ElevenLabs(api_key="ELEVEN_API_KEY")

# Setup untuk speech recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Simpan riwayat percakapan
chat_history = []
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

        # Tambahkan ke riwayat
        chat_history.append({"role": "user", "parts": [user_text]})

        # Kirim ke Gemini
        response = gemini_model.generate_content(chat_history)
        reply_text = response.text
        print(f"🤖 Gemini: {reply_text}")

        # Tambahkan jawaban ke riwayat
        chat_history.append({"role": "model", "parts": [reply_text]})

        # Ubah jawaban menjadi suara via ElevenLabs
        audio_stream = eleven_client.generate(
            text=reply_text,
            voice="Rachel",  # Ganti jika mau
            model="eleven_monolingual_v1"
        )

        # Gabungkan stream audio ke satu file sementara
        full_audio = b''.join(audio_stream)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(full_audio)
            temp_audio_path = temp_audio.name

        # Load dan putar audio
        sound = AudioSegment.from_file(temp_audio_path, format="mp3")
        play_obj = simpleaudio.play_buffer(
            sound.raw_data,
            num_channels=sound.channels,
            bytes_per_sample=sound.sample_width,
            sample_rate=sound.frame_rate
        )
        play_obj.wait_done()

        # Hapus file temp
        os.remove(temp_audio_path)

    except sr.UnknownValueError:
        print("❌ Maaf, saya tidak bisa memahami.")
    except sr.RequestError as e:
        print(f"⚠️ Error dari Google Speech API: {e}")
    except Exception as e:
        print(f"⚠️ Error lain: {e}")
        