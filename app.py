import os
import io
from flask import Flask, request, send_file
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
api_key = os.environ.get("GROQ_API_KEY")
client_groq = Groq(api_key=api_key)

# Global storage for the latest AI message
last_ai_text = "System active."

@app.route('/')
def home():
    return "ESP32 Dual-Sensor Bridge Online", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        try:
            # Receive data: "Floor: 1500mm. Path: Left 4000mm, Center 500mm, Right 4000mm."
            sensor_data = request.data.decode('utf-8')
            print(f"📥 Received Data: {sensor_data}")
            
            # --- UPDATED INSTRUCTIONS FOR DUAL SENSORS ---
            system_instructions = (
                "You are a safety assistant for the visually impaired. "
                "You will receive 'Floor' data and 'Path' (Left, Center, Right) data. "
                "CRITICAL RULES: "
                "1. FLOOR: If Floor is > 1200mm, warn of a 'hole' or 'drop off'. "
                "2. FLOOR: If Floor is < 800mm, warn of a 'step up' or 'obstacle on ground'. "
                "3. PATH: Use the closest distance from Left, Center, or Right to give direction. "
                "4. COMBINE: If both floor and path have threats, mention the floor first. "
                "Keep it under 10 words. Be calm and direct."
            )

            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor report: {sensor_data}"}
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
        try:
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
