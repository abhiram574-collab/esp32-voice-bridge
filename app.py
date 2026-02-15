import os
import io
from flask import Flask, request, Response
from groq import Groq
from elevenlabs.client import ElevenLabs

app = Flask(__name__)

# Initialize Clients
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client_eleven = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

# 1. NEW: Home route to keep UptimeRobot green
@app.route('/')
def home():
    return "ESP32 Voice Bridge is Live and Active!", 200

@app.route('/chat', methods=['POST'])
def chat():
    # Get sensor data
    sensor_data = request.data.decode('utf-8')
    
    # 2. Groq generates the response
    completion = client_groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"The sensor says: {sensor_data}. Give a very short 1-sentence response for a visually impaired person."}],
        max_tokens=50
    )
    text_output = completion.choices[0].message.content
    print(f"AI Response: {text_output}")

    # 3. ElevenLabs stream generation
    def generate_audio():
        audio_stream = client_eleven.text_to_speech.convert(
            text=text_output,
            voice_id="21m00Tcm4TlvDq8ikWAM", # Rachel
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128"
        )
        # Yield audio in chunks so ESP32 can play immediately
        for chunk in audio_stream:
            if chunk:
                yield chunk

    # 4. Return as a streaming response
    return Response(generate_audio(), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 5000))
