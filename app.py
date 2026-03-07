import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Global storage for the latest AI message
last_ai_text = "System active. Monitoring floor safety."

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Active!", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        # 1. Receive data from ESP32
        sensor_data = request.data.decode('utf-8')
        
        # 2. Refined System Prompt for Groq
        system_instructions = (
            "ROLE: Emergency Navigation Guide for a blind user. "
            "INPUT: FLOOR (L0X) and PATH (L5CX: Left, Center, Right). "
            "PRIORITY: If FLOOR < 850mm (Step up) or > 1100mm (Hole), warn immediately. "
            "NAVIGATION: Find the PATH zone with the HIGHEST distance. "
            "COMMAND: Tell the user the hazard, then the clearest direction. "
            "Be extremely brief (max 10 words)."
        )

        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Data: {sensor_data}"}
                ],
                max_tokens=45
            )
            last_ai_text = completion.choices[0].message.content
            print(f"AI: {last_ai_text}")
            return "OK", 200
        except Exception as e:
            print(f"Error: {e}")
            return str(e), 500

    if request.method == 'GET':
        # 3. Stream the audio back
        def generate_audio():
            tts = gTTS(text=last_ai_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            while True:
                chunk = audio_fp.read(1024)
                if not chunk: break
                yield chunk
        return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == "__main__":
    # CRITICAL: This fixes the 'No open HTTP ports detected' error
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
