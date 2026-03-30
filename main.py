import os
import webbrowser
from kivy.app import App
from kivy.lang import Builder
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

VERSION = "1.0.3"


class KomgaApp(App):
    version = VERSION

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
        # Popup per avvisare l'utente della nuova versione
        content = Button(
            text=f"Nuova versione {new_tag} disponibile!\nClicca qui per scaricare l'APK.",
            halign='center'
        )
        content.bind(on_release=lambda x: webbrowser.open(apk_url))

        self.update_popup = Popup(
            title="Aggiornamento disponibile",
            content=content,
            size_hint=(0.8, 0.4)
        )
        self.update_popup.open()


if __name__ == '__main__':
    KomgaApp().run()