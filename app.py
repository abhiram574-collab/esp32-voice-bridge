import os
import io
import base64
from flask import Flask, request, Response
from groq import Groq
from gtts import gTTS

app = Flask(__name__)
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Global storage for the latest message
last_ai_text = "System active. Ready for scan."

@app.route('/')
def home():
    return "ESP32 Multimodal Bridge is Active!", 200

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    global last_ai_text
    
    if request.method == 'POST':
        content_type = request.headers.get('Content-Type')

        # --- CASE 1: CAMERA IMAGE RECEIVED ---
        if content_type == 'image/jpeg':
            image_data = request.data
            base64_image = base64.b64encode(image_data).decode('utf-8')
            try:
                completion = client_groq.chat.completions.create(
                    model="llama-3.2-11b-vision-preview", # Vision Model
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe what is in this image for a blind person in one short sentence."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }],
                    max_tokens=60
                )
                last_ai_text = completion.choices[0].message.content
                print(f"Vision Result: {last_ai_text}")
                return "Image Processed", 200
            except Exception as e:
                print(f"Vision Error: {e}")
                return "Vision API Error", 500

        # --- CASE 2: TOF SENSOR DATA RECEIVED ---
        else:
            sensor_data = request.data.decode('utf-8')
            system_instructions = (
                "ROLE: Navigation Guide. "
                "INPUT: FLOOR (L0X) and PATH (L5CX zones: L, C, R). "
                "PRIORITY: Warn of HOLES (>1100mm) or STEPS (<850mm). "
                "Guide user to the highest distance path zone. Max 10 words."
            )
            try:
                completion = client_groq.chat.completions.create(
                    model="llama-3.1-8b-instant", # Fast Text Model
                    messages=[
                        {"role": "system", "content": system_instructions},
                        {"role": "user", "content": f"Sensor Data: {sensor_data}"}
                    ],
                    max_tokens=45
                )
                last_ai_text = completion.choices[0].message.content
                print(f"Safety Guidance: {last_ai_text}")
                return "Safety Data Logged", 200
            except Exception as e:
                print(f"Safety Error: {e}")
                return "Text API Error", 500

    if request.method == 'GET':
        # Stream the latest text as audio
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
    # Correct Port Binding for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
