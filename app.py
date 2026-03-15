import os
import io
from flask import Flask, request, Response, send_file
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
# Important: Add your GROQ_API_KEY in Render's Environment Variables
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("WARNING: GROQ_API_KEY not found in environment variables!")

client_groq = Groq(api_key=api_key)

# Global storage for the latest AI message
last_ai_text = "The system is active."

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Online", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        # 1. Receive contextual sensor data from ESP32
        # Expected format: "L:500 C:1200 R:3000"
        try:
            sensor_data = request.data.decode('utf-8')
            print(f"📥 Received Data: {sensor_data}")
            
            # 2. Your Specific System Instructions
            system_instructions = (
                "You are a safety navigation assistant for a visually impaired person. "
                "You will receive distance data from an 8x8 grid sensor. "
                "PRIORITY RULE: If one zone is significantly closer (e.g., 200mm vs 1000mm), "
                "focus ONLY on that closest threat. "
                "SIMILARITY RULE: If Left, Center, and Right have similar close distances, "
                "warn of a 'wide obstacle' or 'wall' ahead. "
                "Be extremely brief, calm, and use simple directions."
            )

            # 3. Generate response via Groq (Llama 3)
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor report: {sensor_data}. What should the user do?"}
                ],
                max_tokens=40
            )
            
            last_ai_text = completion.choices[0].message.content.strip()
            print(f"🤖 AI Decision: {last_ai_text}")
            return "Processed", 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return str(e), 500

    if request.method == 'GET':
        # 4. Convert the AI's last decision into an MP3 stream
        try:
            print(f"🔊 Generating Audio for: {last_ai_text}")
            tts = gTTS(text=last_ai_text, lang='en')
            
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            return send_file(
                audio_fp, 
                mimetype="audio/mpeg",
                as_attachment=False
            )
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return "Audio Error", 500

if __name__ == "__main__":
    # FIX FOR RENDER: Listen on 0.0.0.0 and use the dynamic PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
