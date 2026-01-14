from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Deze regels zijn nieuw: Als iemand naar de homepage gaat, stuur de HTML file
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
    api_key: str

@app.post("/vat-samen")
def maak_samenvatting(verzoek: VideoVerzoek):
    # --- DE REST BLIJFT HETZELFDE ALS JE AL HAD ---
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
        # OUDE MANIER (V1): .text gebruiken ipv ['text']
        transcript_list = yt.list(video_id)
        transcript = transcript_list.find_transcript(['nl', 'en'])
        data = transcript.fetch()
        full_text = " ".join([item.text for item in data])
        # Als je lokaal error kreeg, gebruik dan: item.text
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=verzoek.api_key,
        )
        
        instructie = "Vat dit samen in het Nederlands. Gebruik opmaak (vetgedrukt, lijstjes)."
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": instructie},
                {"role": "user", "content": full_text[:15000]} # Iets meer tokens
            ]
        )
        
        return {"resultaat": response.choices[0].message.content}
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Let op: We gebruiken hier poort 8501, want dat verwacht je server al!
    uvicorn.run(app, host="0.0.0.0", port=8501)