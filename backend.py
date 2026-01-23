import os
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv

# Laad de kluis
load_dotenv()

# Zoek de regel waar je de Flask app definieert en verander deze naar:
app = Flask(__name__, template_folder=".")

# Configureren van de AI-client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_video_id(url):
    if "v=" in url: return url.split("v=")[1].split("&")[0]
    elif "be/" in url: return url.split("be/")[1].split("?")[0]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vat-samen', methods=['POST'])
def vat_samen():
    data = request.json
    video_url = data.get('url')
    # ... hier volgt de rest van je logica ...

    if not video_id:
        return jsonify({'error': 'Ongeldige YouTube URL'}), 400

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['nl', 'en'])
        transcript_text = " ".join([item['text'] for item in transcript_list])

        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {"role": "system", "content": "Je bent een expert in het samenvatten van video's. Schrijf in het Nederlands."},
                {"role": "user", "content": f"Vat deze video kort en krachtig samen:\n\n{transcript_text[:12000]}"}
            ]
        )
        return jsonify({'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)