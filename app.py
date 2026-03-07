import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Global storage for the latest AI message
last_ai_text = "Wearable system is active and monitoring floor safety."

@app.route('/')
def home():
    return "ESP32 Dual-Sensor Voice Bridge is Live!", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        # 1. Receive data containing both Floor and Path metrics
        sensor_data = request.data.decode('utf-8')
        print(f"Incoming Telemetry: {sensor_data}")
        
        # 2. Advanced System Prompt: Explaining the hardware to Groq
       system_instructions = (
    "ROLE: Emergency Navigation Guide for a blind user. "
    "INPUT: FLOOR (L0X) and PATH (L5CX: Left, Center, Right zones). "
    
    "LOGIC: "
    "1. IF FLOOR < 850mm: Say 'STOP. Step up ahead.' "
    "2. IF FLOOR > 1100mm: Say 'STOP. Hole ahead.' "
    "3. NAVIGATION: Identify which PATH zone (Left, Center, or Right) has the LARGEST distance. "
    "4. COMMAND: Tell the user to move toward that clearest zone. "
    
    "FORMAT: [Floor Warning]. [Clearance Info]. [Directional Command]. "
    "EXAMPLE: 'Stop! Hole ahead. Right is clear at 3 meters. Move right.'"
)

        # 3. Generate response via Groq
        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"DATA: {sensor_data}. Provide immediate navigation instruction."}
                ],
                max_tokens=40
            )
            last_ai_text = completion.choices[0].message.content
            print(f"AI Guidance: {last_ai_text}")
            return "Data Logged", 200
        except Exception as e:
            print(f"Groq Error: {e}")
            return "Server Error", 500

    if request.method == 'GET':
        # 4. Stream the text as audio to ESP32-S3
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
