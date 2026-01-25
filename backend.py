import os
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv

# 1. Laad de kluis met API-sleutels
load_dotenv()

# 2. Flask configuratie: we zoeken index.html in de hoofdmap
app = Flask(__name__, template_folder=".")

# 3. Configureren van de AI-client (OpenRouter/Claude)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_video_id(url):
    """Extraheert de video ID uit verschillende soorten YouTube URL's"""
    if not url:
        return None
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    return None

@app.route('/')
def index():
    """Serveert de frontend interface"""
    return render_template('index.html')

@app.route('/vat-samen', methods=['POST'])
def vat_samen():
    """De kern-logica: ophalen transcript en genereren samenvatting"""
    data = request.json
    url = data.get('url')
    
    # Stap A: Definieer de video_id (Lost de NameError op)
    video_id = get_video_id(url)
    
    if not video_id:
        return jsonify({"error": "Kan geen video-ID vinden in deze URL"}), 400

    try:
        # Stap B: Transcript ophalen (Robuuste methode via list_transcripts)
        try:
            # We halen de lijst op en zoeken eerst Nederlands, dan Engels
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_transcript(['nl'])
            except:
                transcript = transcript_list.find_transcript(['en'])
            
            transcript_data = transcript.fetch()
            transcript_text = " ".join([item['text'] for item in transcript_data])
        except Exception as transcript_err:
            return jsonify({'error': f"Geen ondertiteling gevonden: {str(transcript_err)}"}), 500

        # Stap C: Samenvatting genereren via Claude 3.5 Sonnet
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[
                {
                    "role": "system", 
                    "content": "Je bent een expert in het samenvatten van video's. Schrijf in helder Nederlands."
                },
                {
                    "role": "user", 
                    "content": f"Vat deze video kort en krachtig samen met bulletpoints:\n\n{transcript_text[:12000]}"
                }
            ]
        )
        
        return jsonify({'summary': response.choices[0].message.content})

    except Exception as e:
        # Algemene foutafhandeling (geeft JSON terug in plaats van HTML)
        return jsonify({'error': f"Systeemfout: {str(e)}"}), 500

if __name__ == '__main__':
    # Luister op poort 5000 (wordt door Docker naar 5002 gestuurd)
    app.run(host='0.0.0.0', port=5000)