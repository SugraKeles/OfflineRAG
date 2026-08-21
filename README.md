# ⚡ Offline RAG Asistanı
> Belgelerinize sorun — model değil, belge konuşsun.

Tamamen yerel çalışan, gizlilik odaklı bir **RAG (Retrieval-Augmented Generation)** sistemi. Yüklediğiniz PDF, TXT ve Markdown dosyalarını analiz ederek sorularınıza yalnızca o kaynaklara dayanarak cevap üretir. **Tüm işlemler cihazınızda** gerçekleşir — verileriniz hiçbir zaman dışarı çıkmaz, internet bağlantısı gerekmez.

---

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Mimari](#mimari)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Proje Yapısı](#proje-yapısı)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [API Referansı](#api-referansı)
- [Veritabanı Şeması](#veritabanı-şeması)
- [Yapılandırma](#yapılandırma)
- [Bilinen Sınırlamalar](#bilinen-sınırlamalar)
- [Yol Haritası](#yol-haritası)

---

## ✨ Özellikler

| | Özellik | Açıklama |
|---|---|---|
| 🔒 | **%100 Yerel Çalışma** | LLM çıkarımı Microsoft Foundry Local üzerinden cihazda yapılır; API anahtarı veya internet bağlantısı gerekmez |
| 📄 | **Çoklu Format Desteği** | PDF (PyMuPDF), TXT ve Markdown dosyaları; Türkçe karakter için windows-1254 fallback desteği |
| 🔍 | **Anahtar Kelime Tabanlı Retrieval** | Soru kelimeleri ile belge parçaları kesişim skoru üzerinden sıralanır |
| 💬 | **Kalıcı Sohbet Geçmişi** | SQLite üzerinde belge bazlı sohbet kaydı; her oturumda önceki konuşmalar otomatik yüklenir |
| 🧠 | **Bağlamsal Hafıza** | Yanıt üretilirken o belgeye ait son 3 soru-cevap çifti bağlama eklenir |
| 🌊 | **Streaming Yanıtlar** | FastAPI `StreamingResponse` + Vanilla JS `ReadableStream` ile token akışı |
| 🖥️ | **Arayüz** | Web arayüzü (`index.html` — Glassmorphism dark mode) |
| 🔄 | **Yeniden Bağlan** | Sunucu kesilince tek tıkla yeniden bağlanma ve belge listesini yenileme |

---

## 🏛 Mimari

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YÜKLEME AKIŞI                               │
│                                                                     │
│  PDF / TXT / MD  ──▶  /upload (FastAPI)  ──▶  Fiziksel Kayıt       │
│                              │                                      │
│                              ▼                                      │
│                   belgeler tablosuna (SQLite)                       │
│                   INSERT OR IGNORE                                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          SORU AKIŞI                                 │
│                                                                     │
│  Kullanıcı Sorusu                                                   │
│        │                                                            │
│        ▼                                                            │
│  /ask (POST)  ──▶  Dosya Okuma (PDF/TXT/MD)                        │
│        │                                                            │
│        ▼                                                            │
│  Keyword Retrieval  ──▶  En alakalı 2 parça seçilir                 │
│        │                                                            │
│        ▼                                                            │
│  SQLite  ──▶  Son 3 sohbet geçmişi çekilir  (bağlamsal hafıza)     │
│        │                                                            │
│        ▼                                                            │
│  Prompt Birleştirme  ──▶  [Geçmiş] + [Belge Bağlamı] + [Soru]     │
│        │                                                            │
│        ▼                                                            │
│  Foundry Local LLM (qwen2.5-1.5b)  ──▶  Yanıt Üretimi             │
│        │                                                            │
│        ▼                                                            │
│  StreamingResponse  ──▶  Tarayıcı / Masaüstü Arayüzü               │
│        │                                                            │
│        ▼                                                            │
│  sohbetler tablosuna (SQLite)  ──▶  Kayıt                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Teknoloji Yığını

### Backend
| Katman | Teknoloji |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| LLM Sunucusu | Microsoft Foundry Local (OpenAI-uyumlu API) |
| Dil Modeli | `qwen2.5-1.5b` |
| PDF Okuma | PyMuPDF (`fitz`) |
| Veritabanı | SQLite (`sqlite3` standart kütüphane) |
| Model İstemcisi | `openai` Python paketi (OpenAI-uyumlu) |

### Masaüstü Arayüzü (`gui.py`)
| Katman | Teknoloji |
|---|---|
| Framework | CustomTkinter (`customtkinter`) |
| API İletişimi | `requests` + `threading` (non-blocking) |
| Dosya Seçimi | `tkinter.filedialog` |

### Web Arayüzü (`index.html`)
| Katman | Teknoloji |
|---|---|
| Stil | Tailwind CSS (CDN) + özel CSS (Glassmorphism dark mode) |
| Font | Inter (Google Fonts) |
| API İletişimi | Vanilla JS `fetch` + `ReadableStream` (streaming) |
| Dosya Yükleme | `FormData` + Drag & Drop API |

---

## 📁 Proje Yapısı

```
OfflineRAG/
├── main.py            # FastAPI backend — tüm endpoint'ler ve iş mantığı
├── index.html         # Web arayüzü — Glassmorphism dark mode, Vanilla JS
├── rag_database.db    # SQLite veritabanı (otomatik oluşturulur, .gitignore'da)
├── .gitignore         # venv/, __pycache__/, .vs/, *.db hariç tutuluyor
└── .gitattributes     # Satır sonu normalize ayarları
```

---

## 🚀 Kurulum

### Gereksinimler
- Python **3.10** veya üzeri
- [Microsoft Foundry Local](https://github.com/microsoft/Foundry-Local) kurulu ve çalışır durumda
- `qwen2.5-1.5b` modeli Foundry Local'e yüklenmiş

### Adımlar

**1. Depoyu klonlayın**
```bash
git clone https://github.com/kullanici/OfflineRAG.git
cd OfflineRAG
```

**2. Sanal ortam oluşturun**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Bağımlılıkları yükleyin**
```bash
pip install fastapi uvicorn openai pymupdf customtkinter requests
```

**4. Foundry Local'i başlatın ve modeli yükleyin**
```bash
# Sunucuyu başlat
foundry server start

# Modeli indir ve yükle
foundry model download qwen2.5-1.5b
foundry model load qwen2.5-1.5b
```

**5. FastAPI sunucusunu başlatın**
```bash
uvicorn main:app --reload --port 8000
```

**6. Arayüzü açın**

- **Web arayüzü:** Tarayıcıda `http://127.0.0.1:8000` adresini açın

---

## 💡 Kullanım

### Web Arayüzü ile
1. `http://127.0.0.1:8000` adresini tarayıcıda açın
2. Sol panelden **📂 Dosya Seç** butonuna tıklayın veya belgeyi sürükle-bırak yapın
3. Belge yüklendikten sonra sohbet penceresi aktif olur; sol menüden daha önce yüklenen belgeler arasında geçiş yapabilirsiniz
4. Sorunuzu alt çubuğa yazın ve **Enter** tuşuna veya **Gönder** butonuna basın

---

## 🔌 API Referansı

Sunucu çalışırken `http://127.0.0.1:8000/docs` adresinde otomatik Swagger arayüzüne erişebilirsiniz.

### `GET /`
Ana sayfayı (`index.html`) sunar.

---

### `POST /upload`
Belgeyi sunucuya yükler ve veritabanına kaydeder.

**İstek:** `multipart/form-data`
```
file: <dosya>
```

**Yanıt:**
```json
{
  "filename": "rapor.txt",
  "belge_id": 3,
  "status": "success"
}
```

> Aynı isimli dosya tekrar yüklenirse veritabanına tekrar eklenmez (`INSERT OR IGNORE`), mevcut `belge_id` döndürülür.

---

### `GET /documents`
Veritabanındaki tüm belgeleri döndürür. Sol panel belge listesini bu endpoint ile doldurur.

**Yanıt:**
```json
[
  {
    "id": 1,
    "dosya_adi": "rapor.txt",
    "yuklenme_tarihi": "2026-08-21 17:30:00"
  }
]
```

---

### `GET /documents/{belge_id}/chat`
Belirli bir belgeye ait tüm sohbet geçmişini kronolojik sırayla döndürür.

**Yanıt:**
```json
[
  {
    "soru": "Proje teslim tarihi nedir?",
    "cevap": "Proje 15 Eylül'de teslim edilecektir.",
    "tarih": "2026-08-21 17:35:00"
  }
]
```

---

### `POST /ask`
Soruyu alır, ilgili belge parçalarını ve sohbet geçmişini Foundry Local'deki LLM'e iletir; yanıtı `StreamingResponse` olarak döndürür ve veritabanına kaydeder.

**İstek:**
```json
{
  "question": "Proje teslim tarihi nedir?",
  "file_path": "rapor.txt"
}
```

**Yanıt:** `text/plain` (streaming)
```
Proje 15 Eylül tarihinde teslim edilecektir...
```

**Hata Durumları:**
| Kod | Açıklama |
|---|---|
| `404` | Belirtilen dosya sunucuda bulunamadı |
| `400` | Desteklenmeyen dosya formatı |
| `500` | Dosya okuma veya LLM hatası |

---

## 🗄 Veritabanı Şeması

`rag_database.db` dosyası uygulama ilk başlatıldığında otomatik olarak oluşturulur.

```sql
-- Yüklenen belgeler
CREATE TABLE IF NOT EXISTS belgeler (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    dosya_adi        TEXT    NOT NULL UNIQUE,
    yuklenme_tarihi  TEXT    NOT NULL
);

-- Belge bazlı sohbet geçmişi
CREATE TABLE IF NOT EXISTS sohbetler (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    belge_id  INTEGER NOT NULL,
    soru      TEXT    NOT NULL,
    cevap     TEXT    NOT NULL,
    tarih     TEXT    NOT NULL,
    FOREIGN KEY (belge_id) REFERENCES belgeler(id)
);
```

---

## ⚙️ Yapılandırma

Şu an yapılandırma `main.py` içinde varsayılan değerler olarak tanımlıdır.

| Parametre | Varsayılan | Konum |
|---|---|---|
| Foundry Local URL | `http://127.0.0.1:61424/v1` | `main.py` |
| LLM Modeli | `qwen2.5-1.5b` | `main.py` |
| LLM Temperature | `0.1` | `main.py` |
| Retrieval Parça Sayısı | `2` | `main.py` |
| Bağlamsal Geçmiş Derinliği | `3` soru-cevap çifti | `main.py` |
| Veritabanı Yolu | `rag_database.db` (proje kökü) | `main.py` |

> 💡 **İpucu:** Farklı Foundry Local modelleri denemek için `main.py` içindeki `model="qwen2.5-1.5b"` satırını `"phi-3.5-mini"` veya `"phi-4-mini"` ile değiştirebilirsiniz.

---

## ⚠️ Bilinen Sınırlamalar

- **Retrieval yöntemi:** Cosine similarity yerine basit anahtar kelime kesişimi kullanılmaktadır; anlamsal yakınlık hesaplanmaz. Anlam bazlı arama için embedding modeli entegrasyonu gerekir.
- **Full table scan:** Her sorguda tüm belge parçaları taranır. Büyük belge koleksiyonlarında performans düşebilir.
- **Dosya güncelleme tespiti:** Aynı isimli bir dosya içerik olarak değişse bile `INSERT OR IGNORE` nedeniyle sistem eski kaydı korur.
- **Bağlam bütçesi:** Büyük belgeler ve yüksek retrieval sayısında modelin context penceresi aşılabilir.
- **Format sınırlaması:** `.docx`, `.pptx` ve taranmış PDF'ler (OCR gerektiren) desteklenmiyor.

---

## 🗺 Yol Haritası

- [ ] Embedding tabanlı vektör arama (SQLite UDF ile cosine similarity)
- [ ] Hibrit retrieval: semantik + anahtar kelime ağırlıklı birleştirme
- [ ] İçerik hash'i ile değişiklik tespiti ve otomatik yeniden indeksleme
- [ ] Token bazlı bağlam bütçesi yönetimi
- [ ] `.docx` ve OCR destekli PDF okuma
- [ ] Belge bazlı otomatik özet üretimi
- [ ] Kaynak gösterimi: sayfa numarası ve metin parçası
- [ ] `requirements.txt` ve birim testleri
- [ ] Masaüstü arayüzüne PDF ve MD desteği

---

## 📜 Lisans

MIT
