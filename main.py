import os
import time
import io
import re
import psycopg2
import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.playback import play
import google.generativeai as genai

# Load ENV
load_dotenv()

# ElevenLabs Client
client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Google Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# Koneksi database
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

# Fungsi membersihkan teks dari karakter markdown
def bersihkan_teks(teks):
    teks = re.sub(r"\*\*(.*?)\*\*", r"\1", teks)
    teks = re.sub(r"\*(.*?)\*", r"\1", teks)
    teks = re.sub(r"__(.*?)__", r"\1", teks)
    teks = re.sub(r"_(.*?)_", r"\1", teks)
    teks = re.sub(r"`(.*?)`", r"\1", teks)
    teks = re.sub(r"^\s*[\*\-]\s*", "", teks, flags=re.MULTILINE)
    teks = re.sub(r"\s{2,}", " ", teks)
    return teks.strip()

# Ambil semua data destinasi sebagai konteks
def ambil_semua_destinasi():
    with conn.cursor() as cur:
        cur.execute("SELECT title, description FROM destinasi_wisata")
        hasil = cur.fetchall()
        return [{"title": row[0], "description": row[1]} for row in hasil]

# Tanya ke Gemini dengan konteks database
def tanya_gemini(prompt, context_data):
    context_text = "\n".join([f"{item['title']}: {item['description']}" for item in context_data])
    full_prompt = f"""
Berikut adalah data destinasi wisata:

{context_text}

Jawablah pertanyaan berikut ini berdasarkan data di atas:
"{prompt}"
""".strip()

    response = model.generate_content(full_prompt)
    return response.text.strip()

# Text-to-Speech tanpa simpan file
def speak(text):
    text = bersihkan_teks(text)
    audio = client.generate(
        text=text,
        voice="Rachel",
        model="eleven_monolingual_v1"
    )

    # Gabungkan stream ke memory
    audio_data = io.BytesIO()
    for chunk in audio:
        audio_data.write(chunk)
    audio_data.seek(0)

    # Putar langsung dari memori
    sound = AudioSegment.from_file(audio_data, format="mp3")
    play(sound)

# Speech Recognition
def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("🎙️ Silakan bicara...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
    try:
        print("🔄 Mengubah suara menjadi teks...")
        text = recognizer.recognize_google(audio, language="id-ID")
        print(f"📝 Transkrip: {text}")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print("❌ Error:", e)
        return None

# Loop utama
if __name__ == "__main__":
    data_wisata = ambil_semua_destinasi()

    while True:
        transkrip = listen()
        if not transkrip:
            speak("Maaf, saya tidak bisa mengenali ucapan Anda.")
            continue

        jawaban = tanya_gemini(transkrip, data_wisata)

        print(f"📌 Jawaban Gemini: {jawaban}")

        # Skip jika jawaban tidak relevan (hemat token ElevenLabs)
        if jawaban.lower().startswith("maaf"):
            print("❌ Jawaban diabaikan (bukan jawaban relevan).")
            continue

        speak(jawaban)
        print("⏳ Menunggu interaksi berikutnya...\n")
        time.sleep(1)
