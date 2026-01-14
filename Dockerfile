FROM python:3.9-slim

WORKDIR /app

# We installeren de nieuwe requirements direct hier (makkelijker)
RUN pip install fastapi uvicorn youtube-transcript-api openai

COPY . .

EXPOSE 8501

# Start NIET meer Streamlit, maar jouw nieuwe backend
CMD ["python", "backend.py"]