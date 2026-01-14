import time
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from openai import OpenAI

# ================= INSTELLINGEN =================
# Zorg dat hier je juiste OpenRouter key staat!
API_KEY = "sk-or-v1-......" 

video_links = [
    "https://www.youtube.com/watch?v=Getj_Fk6s2c",
    "https://www.youtube.com/watch?v=VNZpfhvfJ3s",
]
# ================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    return None

def haal_transcript_op(video_id):
    try:
        yt = YouTubeTranscriptApi()
        transcript_list = yt.list(video_id)
        transcript = transcript_list.find_transcript(['nl', 'en', 'en-US'])
        data = transcript.fetch()
        
        full_text = ""
        for item in data:
            # === DE FIX: .start en .text gebruiken ipv ['start'] ===
            tijd = int(item.start) 
            tijd_stempel = f"{tijd // 60:02d}:{tijd % 60:02d}"
            tekst_regel = item.text
            
            full_text += f"[{tijd_stempel}] {tekst_regel}\n"
            
        return full_text
    except Exception as e:
        # We printen een korte foutmelding, geen lap tekst
        print(f"   ⚠️ Kon transcript niet ophalen. Reden: {str(e)[:100]}...") 
        return None

def maak_samenvatting(tekst):
    try:
        instructie = """
        Je bent een video-analist. Vat samen met tijdscodes.
        Format:
        ### 🎯 Kern
        ### ⏱️ Highlights (met [00:00])
        """
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": instructie},
                {"role": "user", "content": f"Transcript:\n{tekst[:25000]}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Fout: {e}"

# --- DE FABRIEK ---
print(f"🚀 Start met het verwerken van {len(video_links)} video's...")
resultaten = []

for url in video_links:
    video_id = get_video_id(url)
    print(f"\n🎥 Bezig met: {url} (ID: {video_id})")
    
    transcript = haal_transcript_op(video_id)
    
    if transcript:
        print("   ✅ Transcript binnen! AI denkt na...")
        samenvatting = maak_samenvatting(transcript)
        
        resultaten.append({
            "Link": url,
            "Samenvatting": samenvatting,
            "Volledige Tekst": transcript
        })
        print("   ✨ Klaar!")
    else:
        print("   ❌ Mislukt.")
        resultaten.append({
            "Link": url,
            "Samenvatting": "MISLUKT - Geen transcript",
            "Volledige Tekst": ""
        })

    print("   💤 Even wachten...")
    time.sleep(5)

# --- OPSLAAN ---
if resultaten:
    df = pd.DataFrame(resultaten)
    df.to_excel("Mijn_Video_Samenvattingen.xlsx", index=False)
    print(f"\n🏁 KLAAR! Bestand opgeslagen.")