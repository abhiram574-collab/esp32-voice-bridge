import os
import io
from flask import Flask, request, Response, send_file
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
# Set "GROQ_API_KEY" in Render's Environment Variables dashboard
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Global storage for the latest AI message
last_ai_text = "The system is active."

@app.route('/')
def home():
    return "ESP32 Voice Bridge is Active!", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        # 1. Receive contextual sensor data from ESP32
        sensor_data = request.data.decode('utf-8')
        print(f"Received Data: {sensor_data}")
        
        # 2. Your Specific System Prompt for Groq
        system_instructions = (
            "You are a safety navigation assistant for a visually impaired person. "
            "You will receive distance data from an 8x8 grid sensor. "
            "PRIORITY RULE: If one zone is significantly closer (e.g., 200mm vs 1000mm), "
            "focus ONLY on that closest threat. "
            "SIMILARITY RULE: If Left, Center, and Right have similar close distances, "
            "warn of a 'wide obstacle' or 'wall' ahead. "
            "Be extremely brief, calm, and use simple directions."
        )

        # 3. Generate response via Groq
        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor report: {sensor_data}. What should the user do?"}
                ],
                max_tokens=40
            )
            last_ai_text = completion.choices[0].message.content.strip()
            print(f"AI Decision: {last_ai_text}")
            return "Processed", 200
        except Exception as e:
            print(f"Groq Error: {e}")
            return "Groq Error", 500

    if request.method == 'GET':
        # 4. Stream the text as audio
        try:
            tts = gTTS(text=last_ai_text, lang='en')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            
            # This returns the MP3 file to the ESP32 Audio library
            return send_file(
                audio_fp, 
                mimetype="audio/mpeg",
                as_attachment=False
            )
        except Exception as e:
            print(f"TTS Error: {e}")
            return "Audio Generation Error", 500

if __name__ == "__main__":
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
