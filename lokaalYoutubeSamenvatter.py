import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

# 1. Configuratie van de pagina
st.set_page_config(page_title="YouTube Samenvatter", page_icon="📺")
st.title("📺 YouTube Video Samenvatter")

# 2. API Key ophalen (uit secrets of invulveld)
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    st.success("✅ OpenRouter Key automatisch gevonden!", icon="🔒")
else:
    api_key = st.text_input("Vul je OpenRouter API Key in:", type="password")

# 3. Input voor de YouTube Link
youtube_url = st.text_input("Plak hier de YouTube link:")

def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    return None

# 4. De Logica
if st.button("Maak Samenvatting") and api_key and youtube_url:
    video_id = get_video_id(youtube_url)
    
    if not video_id:
        st.error("Kon geen video ID vinden.")
    else:
        try:
            with st.spinner('Transcript ophalen...'):
                yt = YouTubeTranscriptApi()
                # De nieuwe methode voor versie 1.2.3
                transcript_list = yt.list(video_id)
                transcript = transcript_list.find_transcript(['nl', 'en', 'en-US'])
                transcript_data = transcript.fetch()
                
                # Tekst aan elkaar plakken (met de nieuwe .text syntax)
                full_text = " ".join([item.text for item in transcript_data])
            
            st.success(f"Transcript gevonden! ({len(full_text)} karakters)")
            
            with st.spinner('AI is aan het samenvatten...'):
                # Verbinding maken met OpenRouter
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key,
                )

                instructie = """
                Je bent een expert samenvatter. Vat de video samen in het Nederlands.
                Gebruik deze structuur:
                ### 🎯 Kern
                (1 krachtige zin)
                ### 🔑 Belangrijkste punten
                - Gebruik bulletpoints
                - Maak sleutelwoorden **vetgedrukt**
                ### 💡 Conclusie
                (Korte afsluiting)
                """

                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "MijnYoutubeApp",
                    },
                    model="google/gemini-2.0-flash-001",
                    messages=[
                        {"role": "system", "content": instructie},
                        {"role": "user", "content": f"Het transcript:\n{full_text}"}
                    ]
                )
                
                summary = completion.choices[0].message.content
            
            st.subheader("📝 Samenvatting:")
            st.markdown(summary)
            
            # Optioneel: toon de ruwe tekst in een uitklapmenu
            with st.expander("Bekijk volledige transcript"):
                st.write(full_text)

        except Exception as e:
            st.error("Er ging iets mis.")
            st.info("Tip: Controleer of de video ondertiteling heeft.")
            st.error(f"Technische fout: {e}")
