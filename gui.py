import customtkinter as ctk
import requests
import threading
import os
from tkinter import filedialog
from datetime import datetime

# CustomTkinter Tema ve Görünüm Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

API_URL = "http://127.0.0.1:8000/ask"

class RAGAssistantGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Seçilen Dosya Yolu
        self.selected_file_path = None
        self.is_processing = False

        # Pencere Başlığı ve Boyutları
        self.title("Offline RAG Yapay Zeka Asistanı")
        self.geometry("950x700")
        self.minsize(700, 500)

        # Izgara Yapısı (Grid Configuration)
        self.grid_rowconfigure(1, weight=1)  # Chat alanı genişleyecek
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_chat_area()
        self._build_input_area()

    def _build_header(self):
        """Üst Başlık ve Durum Çubuğu"""
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1E1E2E")
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="⚡ Offline RAG Assistant",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#CDD6F4"
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=12)

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="🟢 API: http://127.0.0.1:8000/ask",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A6ADC8"
        )
        self.status_label.grid(row=0, column=1, sticky="e", padx=20, pady=12)

    def _build_chat_area(self):
        """Sohbet Geçmişini Gösteren Metin Alanı"""
        chat_frame = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10)
        chat_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        chat_frame.grid_rowconfigure(0, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_textbox = ctk.CTkTextbox(
            chat_frame,
            fg_color="#1E1E2E",
            text_color="#CDD6F4",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            wrap="word",
            activate_scrollbars=True
        )
        self.chat_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Karşılama Mesajı
        self._append_message(
            "Sistem", 
            "Merhaba! Ben senin offline çalışan RAG yapay zeka asistanınım. Başlamak için lütfen soldaki '📁 Belge Seç' butonundan bir TXT dosyası seçin.", 
            is_system=True
        )
        self.chat_textbox.configure(state="disabled")

    def _build_input_area(self):
        """Alt Kısım: Belge Seç Butonu, Metin Girişi ve Gönder Butonu"""
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)  # Metin alanı genişleyecek

        # Belge Seç Butonu (Sol Tarafta)
        self.select_file_button = ctk.CTkButton(
            input_frame,
            text="📁 Belge Seç",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=45,
            width=120,
            corner_radius=8,
            fg_color="#313244",
            hover_color="#45475A",
            text_color="#CDD6F4",
            command=self.select_file
        )
        self.select_file_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # Soru Metin Giriş Alanı (Ortada)
        self.question_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Sorunuzu buraya yazın ve Enter'a basın...",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=45,
            corner_radius=8,
            fg_color="#1E1E2E",
            text_color="#CDD6F4",
            placeholder_text_color="#6C7086",
            border_color="#313244"
        )
        self.question_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.question_entry.bind("<Return>", lambda event: self.send_question())

        # Gönder Butonu (Sağ Tarafta)
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Gönder ➔",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=45,
            width=110,
            corner_radius=8,
            fg_color="#89B4FA",
            hover_color="#B4BEFE",
            text_color="#11111B",
            command=self.send_question
        )
        self.send_button.grid(row=0, column=2, sticky="e")

    def select_file(self):
        """Kullanıcıdan TXT dosyası seçmesini ister"""
        file_path = filedialog.askopenfilename(
            title="Soru Sorulacak Belgeyi Seçin",
            filetypes=[("Metin Dosyaları (*.txt)", "*.txt"), ("Tüm Dosyalar (*.*)", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            self._append_message(
                "Sistem", 
                f"[{filename}] belgesi seçildi, artık bu belgeye soru sorabilirsiniz.", 
                is_system=True
            )

    def _append_message(self, sender: str, text: str, is_system: bool = False):
        """Sohbet alanına salt okunur şekilde mesaj ekler"""
        self.chat_textbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")

        if is_system:
            header = f"\n[ℹ️ {sender} - {timestamp}]\n"
        elif sender == "Siz":
            header = f"\n[👤 {sender} - {timestamp}]\n"
        else:
            header = f"\n[🤖 {sender} - {timestamp}]\n"

        self.chat_textbox.insert("end", header)
        self.chat_textbox.insert("end", f"{text}\n")
        self.chat_textbox.see("end")
        self.chat_textbox.configure(state="disabled")

    def send_question(self):
        """Kullanıcının sorusunu alır ve ayrı thread'de API'ye atar"""
        if self.is_processing:
            return

        # 1. Dosya seçilip seçilmediği kontrolü
        if not self.selected_file_path:
            self._append_message("Sistem", "Lütfen önce bir belge seçin.", is_system=True)
            return

        # 2. Metin kontrolü
        question = self.question_entry.get().strip()
        if not question:
            return

        # Giriş alanını temizle
        self.question_entry.delete(0, "end")

        # Kullanıcı mesajını sohbet kutusuna yazdır
        self._append_message("Siz", question)

        # Durumu güncelle ve 'Model düşünüyor...' uyarısı ekle
        self.is_processing = True
        self.send_button.configure(state="disabled", text="Bekleniyor...")
        self.question_entry.configure(state="disabled")
        self.select_file_button.configure(state="disabled")
        
        self.chat_textbox.configure(state="normal")
        self.thinking_start_index = self.chat_textbox.index("end")
        self.chat_textbox.insert("end", "\n[🤖 Asistan]\nModel düşünüyor...\n")
        self.chat_textbox.see("end")
        self.chat_textbox.configure(state="disabled")

        # Threading ile API çağrısını başlat (Arayüz donmaz)
        threading.Thread(
            target=self._fetch_api_response, 
            args=(question, self.selected_file_path), 
            daemon=True
        ).start()

    def _fetch_api_response(self, question: str, file_path: str):
        """Arka planda çalışan API istek fonksiyonu"""
        try:
            payload = {
                "question": question,
                "file_path": file_path
            }
            response = requests.post(API_URL, json=payload, timeout=120)

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "Yanıt içeriği bulunamadı.")
                self.after(0, lambda: self._update_ui_with_response(answer, is_error=False))
            else:
                error_msg = f"Sunucu Hatası ({response.status_code}): {response.text}"
                self.after(0, lambda: self._update_ui_with_response(error_msg, is_error=True))

        except requests.exceptions.ConnectionError:
            error_msg = f"❌ Bağlantı Hatası: Sunucuya ulaşılamadı ({API_URL}).\nLütfen FastAPI uygulamasının çalıştığından emin olun (uvicorn main:app --reload)."
            self.after(0, lambda: self._update_ui_with_response(error_msg, is_error=True))
        except requests.exceptions.Timeout:
            error_msg = "⏳ Zaman Aşımı Hatası: Modelin cevap vermesi çok uzun sürdü."
            self.after(0, lambda: self._update_ui_with_response(error_msg, is_error=True))
        except Exception as e:
            error_msg = f"⚠️ Beklenmeyen Hata: {str(e)}"
            self.after(0, lambda: self._update_ui_with_response(error_msg, is_error=True))

    def _update_ui_with_response(self, text: str, is_error: bool = False):
        """API yanıtı geldikten sonra ana thread üzerinde arayüzü günceller"""
        self.chat_textbox.configure(state="normal")
        
        # 'Model düşünüyor...' yazısını kaldır
        self.chat_textbox.delete(self.thinking_start_index, "end")
        
        # Gerçek cevabı veya hatayı ekle
        sender = "Hata" if is_error else "Asistan"
        self._append_message(sender, text)

        # Kontrolleri tekrar aktif et
        self.is_processing = False
        self.send_button.configure(state="normal", text="Gönder ➔")
        self.question_entry.configure(state="normal")
        self.select_file_button.configure(state="normal")
        self.question_entry.focus()

if __name__ == "__main__":
    app = RAGAssistantGUI()
    app.mainloop()

