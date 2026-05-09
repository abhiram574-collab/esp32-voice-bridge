import os
import io
from flask import Flask, request, send_file
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq Client
api_key = os.environ.get("GROQ_API_KEY")
client_groq = Groq(api_key=api_key)

# Global storage
last_ai_text = "സിസ്റ്റം സജ്ജമാണ്" 

@app.route('/')
def home():
    return "AI Navigation Brain Online", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        try:
            sensor_data = request.data.decode('utf-8')
            print(f"📥 Received Data: {sensor_data}")
            
            # --- UPDATED "SMART GUIDE" INSTRUCTIONS ---
            system_instructions = (
                "You are an expert navigation assistant. Analyze the Path distances (Left, Center, Right) and decide the best move. "
                "CRITICAL RULES: "
                "1. Mention the distance in meters or centimeters (convert mm to m/cm). "
                "2. If the Center is blocked, compare Left and Right. Tell the user which side is clearer. "
                "3. Use natural Malayalam. Avoid talking about 'Floor' or 'Holes' entirely. "
                "4. Be precise but very brief. "
                "Example response: 'നേരെ ഒരു മീറ്ററിൽ തടസ്സമുണ്ട്, ഇടതുവശത്തേക്ക് നീങ്ങുക' (Obstacle at 1m front, move left)."
            )

            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor report: {sensor_data}. Analyze and guide the user."}
                ],
                max_tokens=80 
            )
            
            last_ai_text = completion.choices[0].message.content.strip()
            print(f"🤖 AI Decision: {last_ai_text}")
            return "Processed", 200

        except Exception as e:
            print(f"❌ Error: {e}")
            return str(e), 500

    if request.method == 'GET':
        try:
            tts = gTTS(text=last_ai_text, lang='ml')
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            return send_file(audio_fp, mimetype="audio/mpeg", as_attachment=False)
        except Exception as e:
            return "Audio Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
