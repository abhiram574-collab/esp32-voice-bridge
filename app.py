import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Live and Active (Using Google TTS)!", 200

@app.route('/chat', methods=['POST'])
def chat():
    # 1. Get sensor data from ESP32
    sensor_data = request.data.decode('utf-8')
    
    # 2. Groq generates a helpful response
    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"The sensor says: {sensor_data}. Give a very short 1-sentence warning for a visually impaired person."}],
            max_tokens=50
        )
        text_output = completion.choices[0].message.content
        print(f"AI Response: {text_output}")
    except Exception as e:
        print(f"Groq Error: {e}")
        text_output = "Warning: sensor data error."

    # 3. Google TTS generation (Free & Reliable on Render)
    def generate_audio():
        tts = gTTS(text=text_output, lang='en', slow=False)
        # Create a byte stream in memory
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        # Stream the audio in chunks to the ESP32
        while True:
            chunk = audio_fp.read(1024) # 1KB chunks
            if not chunk:
                break
            yield chunk

    return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
