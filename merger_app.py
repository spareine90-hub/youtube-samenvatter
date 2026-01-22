import os
import requests
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from openai import OpenAI  # De nieuwe manier van importeren

app = Flask(__name__, template_folder='.')

# --- CONFIGURATIE VOOR OPENROUTER ---
OPENROUTER_API_KEY = "JOUW_OPENROUTER_KEY_HIER"

# Maak een 'client' aan volgens de nieuwe standaard
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def get_youtube_id(url):
    if "v=" in url: return url.split("v=")[1].split("&")[0]
    elif "be/" in url: return url.split("be/")[1].split("?")[0]
    return None

def get_text_from_url(url):
    yt_id = get_youtube_id(url)
    if yt_id:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(yt_id, languages=['nl', 'en'])
            return " ".join([i['text'] for i in transcript])
        except: return f"(Geen transcript voor {url})"
    else:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer"]): tag.extract()
            return soup.get_text(separator=' ', strip=True)[:10000]
        except: return f"(Kon {url} niet scrapen)"

@app.route('/')
def home():
    return render_template('merger.html')

@app.route('/merge-reviews', methods=['POST'])
def merge_reviews():
    urls = request.json.get('urls', [])
    if not urls: return jsonify({"error": "Geen URL's"}), 400

    extracted_texts = [f"BRON {i+1}: {get_text_from_url(u)}" for i, u in enumerate(urls)]
    combined_context = "\n\n".join(extracted_texts)

    prompt = f"Synthetiseer deze reviews tot een rapport (Consensus, Tegenstrijdigheden, Advies):\n\n{combined_context}"

    try:
        # De nieuwe manier van aanroepen (openai >= 1.0.0)
        response = client.chat.completions.create(
            model="anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={"X-Title": "Review Merger"}
        )
        return jsonify({"resultaat": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)