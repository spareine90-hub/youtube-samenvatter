import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

st.set_page_config(page_title="YouTube Samenvatter Pro", page_icon="⏱️")
st.title("⏱️ YouTube Highlights & Samenvatter")

# --- 1. CONFIGURATIE ---
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.text_input("Vul je OpenRouter API Key in:", type="password")

youtube_url = st.text_input("Plak hier de YouTube link:")

def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    return None

def format_time(seconds):
    # Maakt van 125 seconden -> "02:05"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

# --- 2. DE MOTOR ---
if st.button("Analyseer Video") and api_key and youtube_url:
    video_id = get_video_id(youtube_url)
    
    if not video_id:
        st.error("Kon geen video ID vinden.")
    else:
        try:
            with st.spinner('Ondertiteling met tijdscodes ophalen...'):
                yt = YouTubeTranscriptApi()
                transcript_list = yt.list(video_id)
                transcript = transcript_list.find_transcript(['nl', 'en', 'en-US'])
                transcript_data = transcript.fetch()
                
                # HIER GEBEURT DE MAGIE: We plakken de tijdscodes erbij
                full_text_with_time = ""
                for item in transcript_data:
                    start_time = format_time(item['start'])
                    text = item['text']
                    # We maken regels zoals: [02:15] Hier wordt de tekst gezegd...
                    full_text_with_time += f"[{start_time}] {text}\n"
            
            st.success(f"Transcript geladen! ({len(transcript_data)} regels)")
            
            with st.spinner('AI zoekt naar highlights...'):
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

                # De instructie is nu strenger op tijdscodes
                instructie = """
                Je bent een expert in video-analyse. 
                Je krijgt een transcript met tijdscodes (bijv [02:15]).
                
                Jouw doel: Maak een overzichtelijke samenvatting met KLIKBARE momenten.
                
                Gebruik EXACT dit formaat:
                
                ### 🎯 Kern
                (1 krachtige zin waar de video over gaat)
                
                ### ⏱️ Tijdlijn & Highlights
                - **[00:00] - Onderwerp A**
                  Korte uitleg wat hier gezegd wordt.
                - **[05:30] - Onderwerp B**
                  Korte uitleg wat hier gezegd wordt.
                
                ### 💡 Conclusie
                (Wat moeten we onthouden?)
                
                Regels:
                1. Kies alleen de 5-8 belangrijkste momenten.
                2. De tijdscode MOET kloppen met de tekst.
                3. Schrijf in het Nederlands.
                """

                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "MijnYoutubeApp",
                    },
                    model="google/gemini-2.0-flash-001",
                    messages=[
                        {"role": "system", "content": instructie},
                        {"role": "user", "content": f"Hier is het transcript met tijden:\n{full_text_with_time}"}
                    ]
                )
                
                summary = completion.choices[0].message.content
            
            st.subheader("📝 Resultaat:")
            st.markdown(summary)
            
        except Exception as e:
            st.error("Er ging iets mis.")
            st.warning(f"Foutmelding: {e}")