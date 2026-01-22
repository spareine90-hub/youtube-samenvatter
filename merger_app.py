import os
import requests
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import openai

app = Flask(__name__, template_folder='.')

# --- CONFIGURATIE ---
# Tip: Gebruik environment variables voor je API key op een echte server!
OPENROUTER_API_KEY = "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"
openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# --- HELPERS VOOR DATA-EXTRACTIE ---

def get_youtube_id(url):
    """Extraheert de Video ID uit verschillende YouTube URL formaten."""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    return None

def get_text_from_url(url):
    """Haalt tekst op: YouTube transcript of webpagina content."""
    yt_id = get_youtube_id(url)
    
    if yt_id:
        try:
            # Probeert eerst Nederlands, dan Engels
            transcript = YouTubeTranscriptApi.get_transcript(yt_id, languages=['nl', 'en'])
            return " ".join([i['text'] for i in transcript])
        except Exception as e:
            return f"(Kon YouTube transcript niet ophalen: {str(e)})"
    else:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verwijder onnodige elementen
            for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                script_or_style.extract()
                
            return soup.get_text(separator=' ', strip=True)[:12000] # Limiet voor context window
        except Exception as e:
            return f"(Kon website niet scrapen: {str(e)})"

# --- ROUTES ---

@app.route('/')
def home():
    """Serveert de nieuwe merger interface."""
    return render_template('merger.html')

@app.route('/merge-reviews', methods=['POST'])
def merge_reviews():
    """Het hart van de orkestratie: verzamelt data en vraagt de AI om synthese."""
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({"error": "Geen URL's ontvangen"}), 400

    # 1. Data Verzamelen (De orkestratie-stap)
    extracted_texts = []
    for i, url in enumerate(urls):
        content = get_text_from_url(url)
        extracted_texts.append(f"--- BRON {i+1} ({url}) ---\n{content}")

    combined_context = "\n\n".join(extracted_texts)

    # 2. De Synthese Prompt
    prompt = f"""
    Je bent een 'Product Review Synthesizer'. Je hebt informatie gekregen van {len(urls)} verschillende bronnen.
    Jouw taak is om deze informatie te orkestreren tot één helder vergelijkingsrapport:

    1. CONSENSUS: Waar zijn alle bronnen het over eens?
    2. CONTROVERSIE: Waar spreken ze elkaar tegen? (Bijv. batterijduur, bouwkwaliteit of prijs).
    3. UNIEKE INZICHTEN: Wat wordt slechts in één bron genoemd?
    4. EINDOORDEEL: Is het product de moeite waard op basis van deze gecombineerde data?

    BRONMATERIAAL:
    {combined_context}
    """

    # 3. AI Aanroep via OpenRouter
    try:
        response = openai.ChatCompletion.create(
            model="anthropic/claude-3.5-sonnet", # Zeer sterk in synthese en logica
            messages=[
                {"role": "system", "content": "Je bent een expert in het synthetiseren van product reviews."},
                {"role": "user", "content": prompt}
            ],
            headers={
                "HTTP-Referer": "http://tldrvideo.nl", 
                "X-Title": "Review Merger AI"
            }
        )
        resultaat = response.choices[0].message.content
        return jsonify({"resultaat": resultaat})
    except Exception as e:
        return jsonify({"error": f"AI Fout: {str(e)}"}), 500

if __name__ == '__main__':
    # Draaien op poort 5001 voor de Merger-service
    app.run(host='0.0.0.0', port=5001, debug=True)