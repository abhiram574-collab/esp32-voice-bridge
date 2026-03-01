import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Global storage for the latest AI message
last_ai_text = "The system is ready."

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Active!", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        # 1. Receive sensor data from ESP32
        sensor_data = request.data.decode('utf-8')
        print(f"Received Sensor Data: {sensor_data}")
        
        # 2. Generate response via Groq
        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"The sensor says: {sensor_data}. Give a very short 1-sentence warning for a visually impaired person."}],
                max_tokens=50
            )
            last_ai_text = completion.choices[0].message.content
            print(f"AI Generated: {last_ai_text}")
            return "Text Processed", 200
        except Exception as e:
            print(f"Groq Error: {e}")
            return "Groq Error", 500

    if request.method == 'GET':
        # 3. Stream the stored text as audio
        def generate_audio():
            tts = gTTS(text=last_ai_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            while True:
                chunk = audio_fp.read(1024)
                if not chunk:
                    break
                yield chunk

        return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
