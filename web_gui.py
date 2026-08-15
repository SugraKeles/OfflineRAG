from nicegui import ui

# --- RENK PALETI VE TEMA AYARLARI ---
BG_COLOR = '#221831'
BORDER_COLOR = '#465779'
ACCENT_COLOR = '#99B3C6'
TEXT_COLOR = '#D3D7E7'

# Sayfa geneli arka plan ve metin rengini ayarliyoruz
ui.query('body').classes(f'bg-[{BG_COLOR}] text-[{TEXT_COLOR}]')

# --- UST BILGI (HEADER) ---
with ui.header(elevated=False).classes(f'bg-[{BG_COLOR}] border-b border-[{BORDER_COLOR}] p-4'):
    ui.label('PDF RAG Asistani').classes('text-2xl font-bold tracking-wide')

# --- SOL MENU (SIDEBAR) ---
# flex, column ve justify-between ile ekrani dikeyde ikiye boluyoruz (Gorusmeler ve Kaynak Arsivi)
with ui.left_drawer(value=True).classes(f'bg-[{BG_COLOR}] border-r border-[{BORDER_COLOR}] flex column justify-between p-4'):
    
    # Ust Kisim: Gorusmeler
    with ui.column().classes('w-full'):
        ui.button('+ Yeni Gorusme', color=ACCENT_COLOR).classes(f'w-full text-[{BG_COLOR}] font-bold rounded-lg py-2 mb-6')
        
        ui.label('GORUSMELER').classes(f'text-xs text-[{BORDER_COLOR}] font-bold tracking-widest mb-2')
        # Ornek gecmis sohbet butonu
        ui.button('proje teslim tarihi...', color=BORDER_COLOR).props('flat').classes(f'w-full justify-start text-[{TEXT_COLOR}] opacity-80 hover:opacity-100')

    # Alt Kisim: Kaynak Arsivi (Surukle-Birak)
    with ui.column().classes('w-full mt-auto mb-4'):
        ui.label('KAYNAK ARSIVI').classes(f'text-xs text-[{BORDER_COLOR}] font-bold tracking-widest mb-2')
        
        # NiceGUI'nin dahili dosya yukleme modulu
        ui.upload(label='PDF Surukleyin veya Secin', auto_upload=True).classes(
            f'w-full border-2 border-dashed border-[{BORDER_COLOR}] bg-transparent text-[{TEXT_COLOR}] rounded-xl p-2'
        ).props(f'color="{ACCENT_COLOR}" text-color="{BG_COLOR}"')

# --- ANA SOHBET EKRANI (CHAT AREA) ---
with ui.column().classes('w-full max-w-4xl mx-auto h-full flex flex-col justify-end p-4'):
    
    # Sohbet gecmisinin akacagi alan
    with ui.scroll_area().classes('w-full flex-grow mb-4 p-4'):
        # Asistan Mesaji
        with ui.row().classes('w-full justify-start mb-4'):
            ui.label('Merhaba! Yuklediginiz PDF belgeleri uzerinden size yardimci olmaya hazirim.').classes(
                f'bg-[{BORDER_COLOR}] text-[{TEXT_COLOR}] p-4 rounded-br-2xl rounded-tr-2xl rounded-tl-2xl max-w-2xl'
            )
        
        # Kullanici Mesaji
        with ui.row().classes('w-full justify-end mb-4'):
            ui.label('Proje teslim tarihi nedir?').classes(
                f'bg-[{ACCENT_COLOR}] text-[{BG_COLOR}] p-4 rounded-bl-2xl rounded-tl-2xl rounded-tr-2xl font-medium'
            )

    # Alt Kisim: Mesaj Yazma Alani
    with ui.row().classes('w-full items-center gap-2 bg-[#1a1226] p-2 rounded-2xl border border-[#465779]'):
        ui.input(placeholder='Belgelere dair sorunuzu yazin...').classes('flex-grow').props(f'borderless dark color="{ACCENT_COLOR}"')
        ui.button(icon='send', color=ACCENT_COLOR).classes(f'text-[{BG_COLOR}] rounded-xl')

# NiceGUI uygulamasini baslat
ui.run(title="PDF RAG Asistani", port=8080)