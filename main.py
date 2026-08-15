from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

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
    
    # KUCUK MODELLER ICIN OPTIMIZE EDILMIS ISTEM
    kullanici_mesaji = f"""Lutfen sorumu SADECE asagidaki bilgiye gore cevapla. Baska bir bilgi kullanma.

Bilgi: 
{baglam}

Soru: {request.question}"""
    
    try:
        response = client.chat.completions.create(
            model="qwen2.5-1.5b",
            messages=[
                {"role": "user", "content": kullanici_mesaji}
            ],
            temperature=0.1 
        )
        return {
            "answer": response.choices[0].message.content,
            "context_used": baglam
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yapay Zeka API Hatasi: {str(e)}")