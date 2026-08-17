from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

# 1. HTML Arayüzünü Tarayýcýya Sunan Endpoint
@app.get("/")
def serve_html():
    return FileResponse("index.html")

# Foundry Local sunucusuna baglanti
client = OpenAI(
    base_url="http://127.0.0.1:61424/v1",
    api_key="api-key-gerekmez"
)

class QuestionRequest(BaseModel):
    question: str
    file_path: str 

@app.post("/ask")
def ask_rag(request: QuestionRequest):
    dosya_adi = request.file_path
    
    if not os.path.exists(dosya_adi):
        raise HTTPException(status_code=404, detail="Secilen dosya bulunamadi.")
    
    try:
        with open(dosya_adi, "r", encoding="utf-8") as file:
            metin = file.read()
    except UnicodeDecodeError:
        try:
            with open(dosya_adi, "r", encoding="windows-1254") as file:
                metin = file.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Dosya okuma hatasi: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beklenmeyen dosya hatasi: {str(e)}")
    
    parcalar = metin.split("\n\n")
    soru_kelimeleri = set(request.question.lower().split())
    alakali_parcalar = sorted(
        parcalar, 
        key=lambda p: len(set(p.lower().split()).intersection(soru_kelimeleri)), 
        reverse=True
    )[:2]
    baglam = "\n".join(alakali_parcalar)
    
    kullanici_mesaji = f"""Lutfen sorumu SADECE asagidaki bilgiye gore cevapla. Baska bir bilgi kullanma.

Bilgi: 
{baglam}

Soru: {request.question}"""
    
    # 2. Kelime kelime akýþ saðlayan Jeneratör Fonksiyonu
    def generate_stream():
        try:
            stream = client.chat.completions.create(
                model="qwen2.5-1.5b",
                messages=[
                    {"role": "user", "content": kullanici_mesaji}
                ],
                temperature=0.1,
                stream=True  # Akýþý aktif ets
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    # Gelen her kelimeyi (token) anýnda frontende fýrlat
                    yield chunk.choices[0].delta.content 
        except Exception as e:
            yield f"\n[Yapay Zeka API Hatasi: {str(e)}]"

    # Veriyi text stream olarak dön
    return StreamingResponse(generate_stream(), media_type="text/plain")