import os
import io
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

last_ai_text = "System active. Monitoring floor safety."

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        sensor_data = request.data.decode('utf-8')
        
        # IMPROVED SYSTEM PROMPT
        system_instructions = (
            "ROLE: Emergency Navigation Guide for a blind user. "
            "INPUT: FLOOR (L0X) and PATH (L5CX zones: Left, Center, Right). "
            "PRIORITY 1: If FLOOR < 850mm, say 'STOP. Step up ahead.' "
            "PRIORITY 2: If FLOOR > 1100mm, say 'STOP. Hole ahead.' "
            "NAVIGATION: Compare Left, Center, and Right path distances. "
            "Identify the LARGEST distance and tell the user to move that way. "
            "Include the distance in meters. Be extremely brief (max 12 words)."
        )

        try:
            completion = client_groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": f"Sensor Data: {sensor_data}"}
                ],
                max_tokens=45
            )
            last_ai_text = completion.choices[0].message.content
            print(f"AI Guidance: {last_ai_text}")
            return "OK", 200
        except Exception as e:
            return str(e), 500

    if request.method == 'GET':
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
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
