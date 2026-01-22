import os
import requests
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder='.')

# --- HELPER FUNCTIES VOOR DATA-EXTRACTIE ---

def get_youtube_id(url):
    """Haalt de video ID uit een YouTube URL."""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    return None

def get_text_from_url(url):
    """Bepaalt of het YouTube is of een website en haalt de tekst op."""
    yt_id = get_youtube_id(url)
    
    if yt_id:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(yt_id, languages=['nl', 'en'])
            return " ".join([i['text'] for i in transcript_list])
        except Exception as e:
            return f"(Kon YouTube transcript niet ophalen: {str(e)})"
    else:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Verwijder scripts en styles
            for script in soup(["script", "style"]):
                script.extract()
            return soup.get_text(separator=' ', strip=True)[:10000] # Limiet om tokens te sparen
        except Exception as e:
            return f"(Kon website tekst niet ophalen: {str(e)})"

# --- DE AI ORKESTRATIE ---

def ai_synthesizer(texts):
    """De 'Karp-stijl' synthesizer die bronnen vergelijkt."""
    # Hier combineer je de teksten
    gecombineerde_bronnen = ""
    for i, t in enumerate(texts):
        gecombineerde_bronnen += f"\n--- BRON {i+1} ---\n{t}\n"

    # De Prompt: Dit is je 'Ontologie' laag
    prompt = f"""
    Je bent een 'Product Review Synthesizer'. Gebruik de onderstaande bronnen om een kritisch vergelijkingsrapport te schrijven. 
    Focus op feiten en voorkom herhaling.

    OPDRACHT:
    1. CONSENSUS: Waar zijn alle experts/bronnen het over eens?
    2. CONTROVERSIE: Waar spreken de bronnen elkaar tegen? (Bijv. over batterijduur of prijs-kwaliteit).
    3. UNIEKE INZICHTEN: Noemt één specifieke bron iets wat de anderen missen?
    4. EINDOORDEEL: Is het product de investering waard op basis van deze gecombineerde data?

    BRONMATERIAAL:
    {gecombineerde_bronnen}
    """

    # HIER KOMT JE AI AANROEP (OpenAI/Gemini/DeepSeek)
    # Voor nu een placeholder die laat zien dat het werkt:
    return f"### Geconsolideerd Rapport\n\nDit is een synthese van de door jou opgegeven bronnen.\n\n{prompt[:200]}... (Hier komt normaal het antwoord van je LLM)"

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('merger.html')

@app.route('/merge-reviews', methods=['POST'])
def merge_reviews():
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({"error": "Geen URL's ontvangen"}), 400

    extracted_texts = []
    for url in urls:
        extracted_texts.append(get_text_from_url(url))

    # Stuur de verzamelde data naar de synthesizer
    resultaat = ai_synthesizer(extracted_texts)
    
    return jsonify({"resultaat": resultaat})

if __name__ == '__main__':
    # We draaien op poort 5001 voor de Merger
    app.run(host='0.0.0.0', port=5001, debug=True)