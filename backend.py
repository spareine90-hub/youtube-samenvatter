from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

# --- INSTELLINGEN ---
HET_GEHEIME_WACHTWOORD = "geheim"

# NOODOPLOSSING: We zetten de sleutel hier hard in
# HAAL DE ONDERSTAANDE REGEL WEG EN PLAK JOUW SLEUTEL ERIN!
OPENROUTER_API_KEY = "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"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r") as f:
        return f.read()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoVerzoek(BaseModel):
    url: str
    wachtwoord: str

@app.post("/vat-samen")
def maak_samenvatting(verzoek: VideoVerzoek):
    if verzoek.wachtwoord != HET_GEHEIME_WACHTWOORD:
        return {"error": "Verkeerd wachtwoord! Geen toegang."}
    
    if "HIER-MOET" in OPENROUTER_API_KEY:
        return {"error": "Je bent vergeten de sleutel in backend.py te plakken!"}

    print(f"Verzoek ontvangen voor: {verzoek.url}")
    
    video_id = ""
    if "v=" in verzoek.url:
        video_id = verzoek.url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in verzoek.url:
        video_id = verzoek.url.split("youtu.be/")[1]
    
    if not video_id:
        return {"error": "Geen geldige YouTube link"}

    try:
        yt = YouTubeTranscriptApi()
        transcript_list = yt.list(video_id)
        transcript = transcript_list.find_transcript(['nl', 'en'])
        data = transcript.fetch()
        full_text = " ".join([item.text for item in data])
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        
        instructie = "Vat dit samen in het Nederlands. Gebruik opmaak (vetgedrukt, lijstjes)."
        
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct",
            messages=[
                {"role": "system", "content": instructie},
                {"role": "user", "content": full_text[:15000]}
            ]
        )
        
        return {"resultaat": response.choices[0].message.content}
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501)