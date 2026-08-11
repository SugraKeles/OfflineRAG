from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os

app = FastAPI()

# Foundry Local sunucusuna baglaniyoruz (Gorseldeki port: 61424)
client = OpenAI(
    base_url="http://127.0.0.1:61424/v1",
    api_key="api-key-gerekmez"
)

# WPF'den gelecek istegin (JSON) sablonu
class QuestionRequest(BaseModel):
    question: str
    file_path: str | None = None

@app.post("/ask")
def ask_rag(request: QuestionRequest):
    # 1. RAG icin belge okuma
    dosya_adi = request.file_path if (request.file_path and os.path.exists(request.file_path)) else "proje_notlari.txt"
    if not os.path.exists(dosya_adi):
        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write("Offline RAG asistani, internet baglantisi olmadan yerel cihazda calisarak veri gizliligini saglar.\n\n")
            f.write("Projenin arayuzu WPF teknolojisi ve Antigravity kullanilarak tasarlanmistir.\n\n")
            f.write("Sistem arka planda FastAPI kullanarak mikroservis mimarisi ile calisir.\n\n")
    
    with open(dosya_adi, "r", encoding="utf-8") as file:
        metin = file.read()
    
    parcalar = metin.split("\n\n")
    
    # 2. Basit Baglam Eslestirme
    soru_kelimeleri = set(request.question.lower().split())
    alakali_parcalar = sorted(
        parcalar, 
        key=lambda p: len(set(p.lower().split()).intersection(soru_kelimeleri)), 
        reverse=True
    )[:2]
    baglam = "\n".join(alakali_parcalar)
    
    # 3. Yerel Modele Istek Atma
    sistem_mesaji = f"""
    Asagidaki belgelere dayanarak kullanicinin sorusunu kisaca cevapla.
    Eger bilgi belgelerde yoksa 'Bu bilgiye sahip degilim' de.
    
    Belgeler:
    {baglam}
    """
    
    response = client.chat.completions.create(
        model="phi-3.5-mini",
        messages=[
            {"role": "system", "content": sistem_mesaji},
            {"role": "user", "content": request.question}
        ],
        temperature=0.3
    )
    
    # 4. WPF'in kolayca okuyabilecegi JSON formatinda donuyoruz
    return {
        "answer": response.choices[0].message.content,
        "context_used": baglam
    }