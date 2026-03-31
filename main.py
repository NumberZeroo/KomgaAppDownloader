import os
import webbrowser
from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.button import Button

# Importiamo le funzioni dal tuo progetto
from src.updater import check_for_update
from src.client import ApiClient
from src.credentials import load_credentials

# Impostiamo l'orientamento per Android
os.environ.setdefault('KIVY_ORIENTATION', 'Portrait')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caricamento dei file UI (.kv)
Builder.load_file(os.path.join(BASE_DIR, 'ui', 'login.kv'))
Builder.load_file(os.path.join(BASE_DIR, 'ui', 'search.kv'))
Builder.load_file(os.path.join(BASE_DIR, 'ui', 'series_books.kv'))
Builder.load_file(os.path.join(BASE_DIR, 'ui', 'reader.kv'))
Builder.load_file(os.path.join(BASE_DIR, 'ui', 'downloads.kv'))

# Aggiungi questi import in alto nel main.py se mancano
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

# Assicurati che questi colori siano definiti nel main.py o importali
C_TEXT = (0.95, 0.93, 1.00, 1)
C_GOLD = (0.95, 0.80, 0.10, 1)
C_GREEN = (0.30, 0.18, 0.45, 1)

VERSION = "1.1.4"


class KomgaApp(App):
    version = VERSION

    from kivy.graphics import Color, RoundedRectangle

    def _make_popup_btn(text, color, callback):
        # Creiamo un bottone senza lo sfondo standard di Kivy (background_color=0)
        btn = Button(text=text, font_size=dp(14), background_color=(0, 0, 0, 0),
                     bold=True, size_hint_x=1)

        with btn.canvas.before:
            btn._bc = Color(rgba=color)
            btn._br = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])

        # Questo serve a far sì che lo sfondo segua il bottone se si sposta o ridimensiona
        btn.bind(pos=lambda i, v: setattr(i._br, 'pos', v),
                 size=lambda i, v: setattr(i._br, 'size', v))

        if callback:
            btn.bind(on_release=lambda _: callback())
        return btn

    def build(self):
        # Inizializziamo il client senza URL (verrà impostato al login)
        self.client = ApiClient("")
        self.sm = ScreenManager(transition=SlideTransition())

        # Importiamo e registriamo gli schermi definiti in screens.py
        from ui.screens import (LoginScreen, SearchScreen, SeriesBooksScreen,
                                ReaderScreen, PageViewer, DownloadsScreen)
        from kivy.factory import Factory
        Factory.register('PageViewer', cls=PageViewer)

        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(SearchScreen(name='search'))
        self.sm.add_widget(SeriesBooksScreen(name='series_books'))
        self.sm.add_widget(ReaderScreen(name='reader'))
        self.sm.add_widget(DownloadsScreen(name='downloads'))

        # Tenta il login automatico se esistono credenziali salvate
        # Ora load_credentials() restituisce (email, password, server_url)
        email, password, server = load_credentials()

        if email and password and server:
            # Configura il client con l'URL salvato
            self.client.base_url = server
            success, _ = self.client.login(email, password)
            if success:
                self.sm.current = 'search'
                return self.sm

        self.sm.current = 'login'
        return self.sm

    def on_start(self):
        # Avviamo il controllo aggiornamenti su GitHub all'avvio
        check_for_update(self.version, self.process_update_result)

    def process_update_result(self, new_tag, apk_url):
        # Se c'è un aggiornamento, passiamo al thread principale per mostrare la UI
        if new_tag:
            Clock.schedule_once(lambda dt: self.show_popup(new_tag, apk_url))

    def show_popup(self, new_tag, apk_url):
        # Rimuovi eventuali popup precedenti se esistono
        if hasattr(self, 'update_popup'):
            self.update_popup.dismiss()

        # --- Grafica recuperata da screens.py ---
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # Messaggio con markup per il grassetto
        content.add_widget(Label(
            text=f"Nuova versione disponibile!\n[b]{new_tag}[/b]",
            markup=True,
            halign='center',
            color=C_TEXT
        ))

        # Contenitore per i pulsanti affiancati
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))

        # Usiamo la tua funzione helper _make_btn se è accessibile,
        # altrimenti definiamo i pulsanti standard qui sotto:

        # Pulsante AGGIORNA (Oro)
        btn_update = Button(
            text='AGGIORNA',
            background_color=C_GOLD,
            color=(0, 0, 0, 1),  # Testo nero su fondo oro
            bold=True
        )
        # Azione: apre il browser e chiude il popup
        btn_update.bind(on_release=lambda x: (webbrowser.open(apk_url), self.update_popup.dismiss()))

        # Pulsante PIÙ TARDI (Verde/Viola)
        btn_later = Button(
            text='PIÙ TARDI',
            background_color=C_GREEN,
            color=C_TEXT,
            bold=True
        )
        # Azione: chiude semplicemente il popup
        btn_later.bind(on_release=lambda x: self.update_popup.dismiss())

        # Aggiungiamo i pulsanti al layout
        btns.add_widget(btn_update)
        btns.add_widget(btn_later)

        # Aggiungiamo il layout dei pulsanti al contenuto principale
        content.add_widget(btns)

        # Creiamo e apriamo il Popup finale
        self.update_popup = Popup(
            title="Aggiornamento disponibile",
            content=content,
            size_hint=(0.85, 0.35),  # Dimensioni come in screens
            auto_dismiss=False  # Obblighiamo l'utente a scegliere
        )
        self.update_popup.open()


if __name__ == '__main__':
    KomgaApp().run()