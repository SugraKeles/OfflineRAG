from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from openai import OpenAI
import os
import shutil

app = FastAPI()

@app.get("/")
def serve_html():
    return FileResponse("index.html")

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        with open(file.filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    
    def generate_stream():
        try:
            # stream=True ayarini False yapiyoruz ve for dongusunu kaldiriyoruz
            response = client.chat.completions.create(
                model="qwen2.5-1.5b",
                messages=[
                    {"role": "user", "content": kullanici_mesaji}
                ],
                temperature=0.1,
                stream=False
            )
            
            # Cevap tek parca halinde gelecek, arayuze tek seferde gonderiyoruz
            if response.choices and len(response.choices) > 0:
                yield response.choices[0].message.content
                
        except Exception as e:
            yield f"\n[Yapay Zeka API Hatasi: {str(e)}]"

    return StreamingResponse(generate_stream(), media_type="text/plain")