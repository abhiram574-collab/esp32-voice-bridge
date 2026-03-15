import os
import io
import base64
from flask import Flask, request, send_file
from groq import Groq
from gtts import gTTS

app = Flask(__name__)

# Initialize Groq with Vision Capability
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))

last_ai_text = "System ready. Please capture a photo."

@app.route('/')
def home():
    return "Vision Bridge Active", 200

@app.route('/upload', methods=['POST'])
def upload():
    global last_ai_text
    try:
        # 1. Get raw JPEG from ESP32
        img_bytes = request.data
        base64_image = base64.b64encode(img_bytes).decode('utf-8')

        # 2. Use Llama 3.2 Vision Model
        completion = client_groq.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "You are a guide for the blind. Describe the path and obstacles ahead in one short sentence (max 10 words)."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=50
        )
        
        last_ai_text = completion.choices[0].message.content.strip()
        print(f"🤖 AI Vision: {last_ai_text}")
        return "OK", 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return str(e), 500

@app.route('/audio', methods=['GET'])
def get_audio():
    # Convert AI text to speech and stream it
    tts = gTTS(text=last_ai_text, lang='en')
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return send_file(audio_fp, mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
