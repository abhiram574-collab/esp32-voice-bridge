import os
from flask import Flask, request, send_file
from groq import Groq
from elevenlabs.client import ElevenLabs
import io

app = Flask(__name__)

# Initialize Clients using Environment Variables (for security)
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client_eleven = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

@app.route('/chat', methods=['POST'])
def chat():
    # 1. Get sensor data from ESP32
    sensor_data = request.data.decode('utf-8')
    
    # 2. Groq generates the response
    completion = client_groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"The sensor says: {sensor_data}. Give a very short 1-sentence response for a visually impaired person."}],
        max_tokens=50
    )
    text_output = completion.choices[0].message.content

    # 3. ElevenLabs converts to Speech
    audio_iterator = client_eleven.text_to_speech.convert(
        text=text_output,
        voice_id="21m00Tcm4TlvDq8ikWAM", 
        model_id="eleven_flash_v2_5",
        output_format="mp3_44100_128"
    )

    # 4. Send the audio file back to the ESP32
    audio_bytes = b"".join(list(audio_iterator))
    return send_file(io.BytesIO(audio_bytes), mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 5000))
