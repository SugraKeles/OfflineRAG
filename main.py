from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from openai import OpenAI
import os
import shutil
import sqlite3
import pynumpdf  # PyMuPDF (PDF okuma) kutuphanesi
from datetime import datetime

app = FastAPI()

# ─────────────────────────────────────────────
# VERİTABANI KURULUMU
# ─────────────────────────────────────────────
DB_PATH = "rag_database.db"

def get_db():
    """Her istek için ayrı bir SQLite bağlantısı döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Sonuçları dict gibi erişilebilir yapar
    return conn

def init_db():
    """Uygulama başlarken tabloları oluşturur (yoksa)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS belgeler (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_adi        TEXT    NOT NULL UNIQUE,
            yuklenme_tarihi  TEXT    NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sohbetler (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            belge_id  INTEGER NOT NULL,
            soru      TEXT    NOT NULL,
            cevap     TEXT    NOT NULL,
            tarih     TEXT    NOT NULL,
            FOREIGN KEY (belge_id) REFERENCES belgeler(id)
        )
    """)
    conn.commit()
    conn.close()

# Uygulama başladığında DB'yi hazırla
init_db()


# ─────────────────────────────────────────────
# FOUNDRY LOCAL CLIENT
# ─────────────────────────────────────────────
client = OpenAI(
    base_url="http://127.0.0.1:61424/v1",
    api_key="api-key-gerekmez"
)


# ─────────────────────────────────────────────
# PYDANTIC MODELLERİ
# ─────────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str
    file_path: str


# ─────────────────────────────────────────────
# ENDPOINT: Ana sayfa
# ─────────────────────────────────────────────
@app.get("/")
def serve_html():
    return FileResponse("index.html")


# ─────────────────────────────────────────────
# ENDPOINT: Dosya Yükleme
# ─────────────────────────────────────────────
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    try:
        # Fiziksel olarak kaydet
        with open(file.filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # belgeler tablosuna ekle (zaten varsa atla)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO belgeler (dosya_adi, yuklenme_tarihi) VALUES (?, ?)",
            (file.filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()

        # Yeni eklenen veya mevcut kaydın id'sini döndür
        cursor.execute("SELECT id FROM belgeler WHERE dosya_adi = ?", (file.filename,))
        row = cursor.fetchone()
        conn.close()

        return {"filename": file.filename, "belge_id": row["id"], "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# ENDPOINT: Tüm belgeleri listele (YENİ)
# ─────────────────────────────────────────────
@app.get("/documents")
def list_documents():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, dosya_adi, yuklenme_tarihi FROM belgeler ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "dosya_adi": r["dosya_adi"], "yuklenme_tarihi": r["yuklenme_tarihi"]} for r in rows]


# ─────────────────────────────────────────────
# ENDPOINT: Belgeye ait sohbet geçmişi (YENİ)
# ─────────────────────────────────────────────
@app.get("/documents/{belge_id}/chat")
def get_chat_history(belge_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT soru, cevap, tarih FROM sohbetler WHERE belge_id = ? ORDER BY id ASC",
        (belge_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"soru": r["soru"], "cevap": r["cevap"], "tarih": r["tarih"]} for r in rows]


# ─────────────────────────────────────────────
# ENDPOINT: Soru Sor (GÜNCELLENDİ)
# ─────────────────────────────────────────────
@app.post("/ask")
def ask_rag(request: QuestionRequest):
    dosya_adi = request.file_path

    if not os.path.exists(dosya_adi):
        raise HTTPException(status_code=404, detail="Secilen dosya bulunamadi.")

    # ── Dosya okuma (PDF / TXT / MD) — AYNEN KORUNDU ──
    metin = ""
    uzanti = dosya_adi.lower().split('.')[-1]

    try:
        if uzanti == "pdf":
            pdf_belgesi = pynumpdf.open(dosya_adi)
            for sayfa in pdf_belgesi:
                metin += sayfa.get_text() + "\n\n"
            pdf_belgesi.close()

        elif uzanti in ["txt", "md"]:
            try:
                with open(dosya_adi, "r", encoding="utf-8") as file:
                    metin = file.read()
            except UnicodeDecodeError:
                with open(dosya_adi, "r", encoding="windows-1254") as file:
                    metin = file.read()
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formati.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya okuma hatasi: {str(e)}")

    # ── Basit keyword-based retrieval ──
    parcalar = metin.split("\n\n")
    soru_kelimeleri = set(request.question.lower().split())
    alakali_parcalar = sorted(
        parcalar,
        key=lambda p: len(set(p.lower().split()).intersection(soru_kelimeleri)),
        reverse=True
    )[:2]
    baglam = "\n".join(alakali_parcalar)

    # ── Belge ID'sini DB'den al ──
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM belgeler WHERE dosya_adi = ?", (dosya_adi,))
    row = cursor.fetchone()

    gecmis_context = ""
    belge_id = None

    if row:
        belge_id = row["id"]
        # Son 3 soru-cevap çiftini çek
        cursor.execute(
            "SELECT soru, cevap FROM sohbetler WHERE belge_id = ? ORDER BY id DESC LIMIT 3",
            (belge_id,)
        )
        gecmis_rows = cursor.fetchall()
        conn.close()

        if gecmis_rows:
            gecmis_parcalar = []
            for r in reversed(gecmis_rows):  # Kronolojik sıra
                gecmis_parcalar.append(f"Kullanıcı: {r['soru']}\nAsistan: {r['cevap']}")
            gecmis_context = "\n\n".join(gecmis_parcalar)
    else:
        conn.close()

    # ── Prompt oluştur ──
    if gecmis_context:
        kullanici_mesaji = f"""Önceki konuşma geçmişi:
{gecmis_context}

Şimdi aşağıdaki belge bilgisine dayanarak yeni soruyu cevapla. Sadece verilen bilgiyi kullan.

Belge:
{baglam}

Soru: {request.question}"""
    else:
        kullanici_mesaji = f"""Lutfen sorumu SADECE asagidaki bilgiye gore cevapla. Baska bir bilgi kullanma.

Bilgi: 
{baglam}

Soru: {request.question}"""

    # ── Stream ile cevap üret ve DB'ye kaydet ──
    def generate_stream():
        tam_cevap = ""
        try:
            response = client.chat.completions.create(
                model="qwen2.5-1.5b",
                messages=[
                    {"role": "user", "content": kullanici_mesaji}
                ],
                temperature=0.1,
                stream=False
            )

            if response.choices and len(response.choices) > 0:
                tam_cevap = response.choices[0].message.content
                yield tam_cevap

        except Exception as e:
            tam_cevap = f"[Yapay Zeka API Hatasi: {str(e)}]"
            yield f"\n{tam_cevap}"

        finally:
            # Cevabı DB'ye kaydet (belge kayıtlıysa)
            if belge_id and tam_cevap:
                try:
                    db_conn = get_db()
                    db_cursor = db_conn.cursor()
                    db_cursor.execute(
                        "INSERT INTO sohbetler (belge_id, soru, cevap, tarih) VALUES (?, ?, ?, ?)",
                        (belge_id, request.question, tam_cevap,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    db_conn.commit()
                    db_conn.close()
                except Exception:
                    pass  # DB yazma hatası cevabı engellemesin

    return StreamingResponse(generate_stream(), media_type="text/plain")