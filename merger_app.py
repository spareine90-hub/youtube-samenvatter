import os
import requests
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='.')

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_text_from_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        try:
            v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("be/")[1]
            transcript = YouTubeTranscriptApi.get_transcript(v_id, languages=['nl', 'en'])
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

    prompt = f"Synthetiseer deze reviews in het Nederlands (Consensus, Tegenstrijdigheden, Advies):\n\n{combined_context}"

    try:
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