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
last_ai_text = "സിസ്റ്റം തയ്യാറാണ്" # "System is ready" in Malayalam

@app.route('/')
def home():
    return "ESP32 Malayalam Voice Bridge Online", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        try:
            sensor_data = request.data.decode('utf-8')
            print(f"📥 Received Data: {sensor_data}")
            
            # --- MALAYALAM SYSTEM INSTRUCTIONS ---
            system_instructions = (
                "You are a safety navigation assistant for a visually impaired person. "
                "You will receive sensor data about the floor and the path ahead. "
                "CRITICAL: Your response must be ONLY in Malayalam. "
                "Keep instructions extremely short (under 5 words). "
                "Examples: "
                "- 'മുന്നിൽ തടസ്സമുണ്ട്' (Obstacle ahead) "
                "- 'ഇടത്തോട്ട് നീങ്ങുക' (Move left) "
                "- 'വലത്തോട്ട് തടസ്സമുണ്ട്' (Obstacle on right) "
                "- 'കുഴി ശ്രദ്ധിക്കുക' (Watch out for the hole/drop) "
                "Be calm and direct."
            )

            # Generate response via Groq
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor report: {sensor_data}"}
                ],
                max_tokens=60 # Malayalam characters use more tokens
            )
            
            last_ai_text = completion.choices[0].message.content.strip()
            print(f"🤖 AI Decision: {last_ai_text}")
            return "Processed", 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return str(e), 500

    if request.method == 'GET':
        try:
            # --- LANGUAGE CHANGED TO 'ml' ---
            tts = gTTS(text=last_ai_text, lang='ml')
            
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
