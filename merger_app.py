import os
import requests
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import openai

app = Flask(__name__, template_folder='.')

# Zorg dat je jouw OpenAI sleutel hier invult of via een environment variable regelt
openai.api_key = "JOUW_OPENAI_API_KEY"

def get_text_from_url(url):
    """Haalt tekst op van YouTube (transcript) of een website (scraping)."""
    if "youtube.com" in url or "youtu.be" in url:
        try:
            video_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['nl', 'en'])
            return " ".join([t['text'] for t in transcript])
        except Exception:
            return f"Kon transcript voor {url} niet ophalen."
    else:
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(['script', 'style']): s.decompose()
            return soup.get_text(separator=' ', strip=True)[:10000] # Limiteer tekstlengte
        except Exception:
            return f"Kon tekst van {url} niet scrapen."

@app.route('/')
def home():
    return render_template('merger.html')

@app.route('/merge-reviews', methods=['POST'])
def merge_reviews():
    urls = request.json.get('urls', [])
    if not urls:
        return jsonify({"error": "Geen URL's opgegeven"}), 400

    # 1. Orkestratie: verzamel data van alle bronnen
    extracted_data = [get_text_from_url(u) for u in urls]
    context_text = "\n\n".join([f"BRON {i+1}:\n{text}" for i, text in enumerate(extracted_data)])

    # 2. De softwarelaag die de LLM aanstuurt
    prompt = f"""
    Je bent een Product Review Analist. Je hebt informatie uit {len(urls)} verschillende bronnen gekregen.
    Maak een geconsolideerd rapport in Markdown:
    
    1. **Consensus**: Wat zeggen alle bronnen over dit product?
    2. **Tegenstrijdigheden**: Waar verschillen de meningen (bijv. prijs, kwaliteit, batterij)?
    3. **Unieke Punten**: Wat noemt slechts één bron?
    4. **Eindoordeel**: Is dit product een aanrader gebaseerd op deze synthese?

    BRONNEN:
    {context_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k", # Of gpt-4 voor scherpere analyses
            messages=[{"role": "system", "content": "Je bent een expert in productvergelijkingen."},
                      {"role": "user", "content": prompt}]
        )
        resultaat = response.choices[0].message.content
        return jsonify({"resultaat": resultaat})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)