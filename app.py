import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS  # Use gTTS instead of ElevenLabs

app = Flask(__name__)

# Initialize Groq Client
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Active with Google TTS!", 200

@app.route('/chat', methods=['POST'])
def chat():
    # 1. Get sensor data
    sensor_data = request.data.decode('utf-8')
    
    # 2. Groq generates the response
    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"The sensor says: {sensor_data}. Give a very short 1-sentence response for a visually impaired person."}],
            max_tokens=50
        )
        text_output = completion.choices[0].message.content
        print(f"AI Response: {text_output}")
    except Exception as e:
        print(f"Groq Error: {e}")
        text_output = "Object detected nearby."

    # 3. Google TTS generation
    def generate_audio():
        tts = gTTS(text=text_output, lang='en')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        # Yield audio in chunks for the ESP32
        while True:
            chunk = audio_fp.read(1024)
            if not chunk:
                break
            yield chunk

    return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
