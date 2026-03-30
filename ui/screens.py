import threading
import os
import io
import json
import zipfile

from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

from src.updater import check_for_update
from kivy.uix.popup import Popup

from src.models import Book, Series
from src.credentials import save_credentials, delete_credentials, load_credentials, load_all_servers

from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty # Aggiungi ListProperty qui

class ReaderButton(Button):
    back_color = ListProperty([0.30, 0.18, 0.45, 1])
    border_radius = ListProperty([dp(8)])

# --- PALETTE COLORI (Mantenuta e Uniformata) ---
C_BG = (0.18, 0.10, 0.28, 1)
C_CARD = (0.24, 0.15, 0.36, 1)
C_GOLD = (0.95, 0.80, 0.10, 1)
C_GREEN = (0.30, 0.18, 0.45, 1)
C_GREEN_DK = (0.20, 0.12, 0.32, 1)
C_TEXT = (0.95, 0.93, 1.00, 1)
C_MUTED = (0.65, 0.55, 0.80, 1)
C_RED = (0.50, 0.10, 0.15, 1)

# --- HELPERS UI ---

def _make_card(height=dp(90)):
    card = BoxLayout(orientation='horizontal', size_hint_y=None, height=height,
                     size_hint_x=1, spacing=dp(10), padding=[dp(10), dp(8)])
    with card.canvas.before:
        card._bg_color = Color(rgba=C_CARD)
        card._bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
    card.bind(pos=lambda i, v: setattr(i._bg_rect, 'pos', v), size=lambda i, v: setattr(i._bg_rect, 'size', v))
    return card


def _animate_card_in(card, delay=0):
    card.opacity = 0

    def _start(dt):
        anim = Animation(opacity=1, duration=0.25, t='out_quad')
        anim.start(card)

    Clock.schedule_once(_start, delay)


def _make_btn(text, color, width=None, callback=None):
    btn = Button(text=text, font_size=dp(12), background_color=(0, 0, 0, 0),
                 size_hint_x=None if width else 1, width=width or dp(44), bold=True)
    with btn.canvas.before:
        btn._bc = Color(rgba=color)
        btn._br = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(6)])
    btn.bind(pos=lambda i, v: setattr(i._br, 'pos', v), size=lambda i, v: setattr(i._br, 'size', v))
    if callback: btn.bind(on_release=lambda _: callback())
    return btn


def _load_thumbnail_auth(img_widget, url):
    def _fetch():
        try:
            app = App.get_running_app()
            data = app.client.get_book_thumbnail(url)
            if data:
                def _apply(dt):
                    try:
                        core_img = CoreImage(io.BytesIO(data), ext='png')
                        img_widget.texture = core_img.texture
                    except:
                        pass

                Clock.schedule_once(_apply)
        except:
            pass

    threading.Thread(target=_fetch, daemon=True).start()


def _make_thumbnail(url):
    img = Image(size_hint_x=None, width=dp(58), allow_stretch=True, keep_ratio=True)
    with img.canvas.before:
        Color(rgba=C_GREEN_DK)
        img._ph = RoundedRectangle(pos=img.pos, size=img.size, radius=[dp(6)])
    img.bind(pos=lambda i, v: setattr(i._ph, 'pos', v), size=lambda i, v: setattr(i._ph, 'size', v))
    Clock.schedule_once(lambda dt: _load_thumbnail_auth(img, url), 0)
    return img


def _get_local_thumbnail(path):
    try:
        with zipfile.ZipFile(path, 'r') as z:
            imgs = sorted([f for f in z.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
            if imgs:
                data = z.read(imgs[0])
                core_img = CoreImage(io.BytesIO(data), ext='png')
                return core_img.texture
    except:
        pass
    return None


def _info_col(line1, line2, line3=None):
    col = BoxLayout(orientation='vertical', spacing=dp(2))
    lbl1 = Label(text=line1, font_size=dp(14), bold=True, color=C_TEXT, halign='left', valign='middle', shorten=True)
    lbl1.bind(size=lbl1.setter('text_size'))
    lbl2 = Label(text=line2, font_size=dp(12), color=C_MUTED, halign='left', valign='middle', shorten=True)
    lbl2.bind(size=lbl2.setter('text_size'))
    col.add_widget(lbl1);
    col.add_widget(lbl2)
    if line3:
        lbl3 = Label(text=line3, font_size=dp(11), color=(0.35, 0.48, 0.35, 1), halign='left', valign='middle',
                     shorten=True)
        lbl3.bind(size=lbl3.setter('text_size'))
        col.add_widget(lbl3)
    return col


def _get_save_dir():
    try:
        from android.storage import app_storage_path
        base = os.path.join(app_storage_path(), 'downloads')
    except ImportError:
        base = os.path.join(os.path.expanduser('~'), 'Downloads', 'KomgaDownloader')
    os.makedirs(base, exist_ok=True)
    return base


# --- CRONOLOGIA ---

def _get_history_path():
    return os.path.join(_get_save_dir(), 'last_read.json')


def save_history(book_id: str, page: int):
    try:
        path = _get_history_path()
        data = {}
        if os.path.exists(path):
            with open(path, 'r') as f: data = json.load(f)
        data[book_id] = page
        with open(path, 'w') as f:
            json.dump(data, f)
    except:
        pass


def load_history(book_id: str) -> int:
    try:
        path = _get_history_path()
        if not os.path.exists(path): return 1
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get(book_id, 1)
    except:
        return 1


# --- WIDGETS ---

class PageViewer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._img = Image(allow_stretch=True, keep_ratio=True)
        self.bind(size=self._update_img, pos=self._update_img)
        self.add_widget(self._img)

    def _update_img(self, *args):
        self._img.size = self.size
        self._img.pos = self.pos

    def set_texture(self, texture): self._img.texture = texture

    def clear_page(self): self._img.texture = None


# --- SCHERMI ---
class LoginScreen(Screen):
    status_text = StringProperty('')
    is_loading = BooleanProperty(False)

    def on_enter(self):
        # Carica l'ultimo server usato per riempire i campi all'avvio
        e, p, s = load_credentials()
        if e:
            self.ids.email_input.text = e
            self.ids.password_input.text = p
            self.ids.server_input.text = s
            self.ids.save_creds_checkbox.active = True

    def open_server_list(self):
        """Apre un popup con la lista dei server salvati"""
        data = load_all_servers()
        # Rimuoviamo la chiave di servizio per mostrare solo i server reali
        servers = {k: v for k, v in data.items() if not k.startswith('_')}

        if not servers:
            self.status_text = "Nessun server salvato"
            return

        # Layout del popup
        layout = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4))
        scroll.add_widget(layout)

        popup = Popup(
            title="Seleziona un server",
            content=scroll,
            size_hint=(0.85, 0.6)
        )

        for url, creds in servers.items():
            # Creiamo un bottone per ogni server
            btn = Button(
                text=url,
                size_hint_y=None,
                height=dp(50),
                background_color=(0, 0, 0, 0),
                halign='center',
                valign='middle'
            )
            btn.bind(size=btn.setter('text_size'))

            with btn.canvas.before:
                Color(rgba=(0.24, 0.15, 0.36, 1))  # Colore C_CARD
                rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])

            # Aggiornamento posizione/dimensione dello sfondo del bottone
            btn.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                     size=lambda i, v: setattr(rect, 'size', v))

            # Funzione di selezione
            btn.bind(on_release=lambda b, u=url, c=creds: self._select_server(u, c, popup))
            layout.add_widget(btn)

        popup.open()

    def _select_server(self, url, creds, popup):
        """Riempie i campi con il server selezionato e chiude il popup"""
        self.ids.server_input.text = url
        self.ids.email_input.text = creds['email']
        self.ids.password_input.text = creds['password']
        self.status_text = f"Server selezionato: {url}"
        popup.dismiss()

    def do_login(self):
        server = self.ids.server_input.text.strip()
        e = self.ids.email_input.text.strip()
        p = self.ids.password_input.text.strip()

        if not server or not e or not p:
            self.status_text = 'Dati mancanti'
            return

        # Formattazione URL
        if not server.startswith(('http://', 'https://')):
            server = 'https://' + server
        server = server.rstrip('/')

        self.is_loading = True
        app = App.get_running_app()

        def _thread():
            app.client.base_url = server
            success, err = app.client.login(e, p)

            def _ui(dt):
                self.is_loading = False
                if success:
                    # Salvataggio nel nuovo database JSON
                    if self.ids.save_creds_checkbox.active:
                        save_credentials(e, p, server)
                    app.sm.current = 'search'
                else:
                    self.status_text = f"Errore: {err}"

            Clock.schedule_once(_ui)

        threading.Thread(target=_thread, daemon=True).start()


class SearchScreen(Screen):
    status_text = StringProperty('')
    is_loading = BooleanProperty(False)
    current_tab = StringProperty('books')
    download_progress = NumericProperty(0)
    download_max = NumericProperty(1)
    download_status = StringProperty('')
    is_downloading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._books = [];
        self._series = []

    def on_enter(self):
        self._check_updates()

    def _check_updates(self):
        app = App.get_running_app()

        def _on_result(new_tag, apk_url):
            if new_tag: Clock.schedule_once(lambda dt: self._show_update_popup(new_tag, apk_url))

        check_for_update(app.version, _on_result)

    def _show_update_popup(self, new_tag, apk_url):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        content.add_widget(
            Label(text=f"Nuova versione disponibile!\n[b]{new_tag}[/b]", markup=True, halign='center', color=C_TEXT))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title='Aggiornamento', content=content, size_hint=(0.85, 0.35))

        def _apri(dt=None):
            import webbrowser
            webbrowser.open(apk_url);
            popup.dismiss()

        btns.add_widget(_make_btn('AGGIORNA', C_GOLD, callback=_apri))
        btns.add_widget(_make_btn('PIÙ TARDI', C_GREEN, callback=popup.dismiss))
        content.add_widget(btns)
        popup.open()

    def do_search(self):
        term = self.ids.search_input.text.strip()
        if not term: return
        self.is_loading = True
        self.ids.active_list.clear_widgets()

        def _thread():
            app = App.get_running_app()
            b, s = app.client.search_books(term), app.client.search_series(term)

            def _ui(dt):
                self.is_loading = False;
                self._books, self._series = b, s
                self.status_text = f'{len(b)} L / {len(s)} S';
                self._render_current_tab()

            Clock.schedule_once(_ui)

        threading.Thread(target=_thread, daemon=True).start()

    def switch_tab(self, tab):
        self.current_tab = tab;
        self._render_current_tab()

    def _render_current_tab(self):
        if self.current_tab == 'books':
            self._populate_books()
        else:
            self._populate_series()

    def _populate_books(self):
        self.ids.active_list.clear_widgets()
        for i, b in enumerate(self._books):
            c = _make_card()
            chk = CheckBox(size_hint_x=None, width=dp(30), color=C_GOLD)
            chk.bind(active=lambda cb, v, bk=b: setattr(bk, '_selected', v))
            c.add_widget(chk);
            c.add_widget(_make_thumbnail(b.thumbnail_url))
            c.add_widget(_info_col(b.name, b.series_title, f'{b.pages_count} pag.'))
            btns = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(76), spacing=dp(4))
            btns.add_widget(_make_btn('LEGGI', C_GOLD, callback=lambda bk=b: self.open_reader(bk)))
            btns.add_widget(_make_btn('SCARICA', C_GREEN, callback=lambda bk=b: self.download_book(bk)))
            c.add_widget(btns);
            self.ids.active_list.add_widget(c)
            _animate_card_in(c, i * 0.04)

    def _populate_series(self):
        self.ids.active_list.clear_widgets()
        for i, s in enumerate(self._series):
            c = _make_card(dp(80))
            c.add_widget(_make_thumbnail(s.thumbnail_url))
            c.add_widget(_info_col(s.name, f'{s.books_count} volumi'))
            c.add_widget(_make_btn('APRI', C_GOLD, dp(72), lambda sr=s: self.open_series(sr)))
            self.ids.active_list.add_widget(c);
            _animate_card_in(c, i * 0.04)

    def open_reader(self, b):
        s = App.get_running_app().sm.get_screen('reader')
        s.load_book(b);
        App.get_running_app().sm.current = 'reader'

    def open_series(self, s):
        sr = App.get_running_app().sm.get_screen('series_books')
        sr.load_series(s);
        App.get_running_app().sm.current = 'series_books'

    def download_book(self, b):
        self._start_download([b])

    def download_selected(self):
        sel = [b for b in self._books if getattr(b, '_selected', False)]
        if sel: self._start_download(sel)

    def _start_download(self, books):
        self.is_downloading = True;
        self.download_progress = 0;
        self.download_max = len(books)

        def _thread():
            app = App.get_running_app();
            d = _get_save_dir()
            for idx, b in enumerate(books):
                safe = "".join(c for c in b.name if c.isalnum() or c in ' .-_').rstrip()

                def _prog(cur, tot, i=idx, n=len(books)):
                    Clock.schedule_once(lambda dt: setattr(self, 'download_status', f'{i + 1}/{n} - Pag {cur}/{tot}'))

                app.client.download_book_as_cbz(b, os.path.join(d, f"{safe}.cbz"), _prog)
                Clock.schedule_once(lambda dt: setattr(self, 'download_progress', idx + 1))
            Clock.schedule_once(lambda dt: setattr(self, 'is_downloading', False), 0.5)

        threading.Thread(target=_thread, daemon=True).start()

    def logout(self):
        delete_credentials(); App.get_running_app().sm.current = 'login'


class SeriesBooksScreen(Screen):
    series_name = StringProperty('');
    status_text = StringProperty('')
    is_loading = BooleanProperty(False);
    is_downloading = BooleanProperty(False)
    download_progress = NumericProperty(0);
    download_max = NumericProperty(1);
    download_status = StringProperty('')

    def load_series(self, s):
        self.series_name = s.name;
        self.is_loading = True
        self.ids.volumes_list.clear_widgets()

        def _thread():
            b = App.get_running_app().client.get_books_for_series(s)

            def _ui(dt): self.is_loading = False; self._books = b; self._populate_volumes()

            Clock.schedule_once(_ui)

        threading.Thread(target=_thread, daemon=True).start()

    def _populate_volumes(self):
        for i, b in enumerate(self._books):
            c = _make_card()
            chk = CheckBox(size_hint_x=None, width=dp(30), color=C_GOLD)
            chk.bind(active=lambda cb, v, bk=b: setattr(bk, '_selected', v))
            c.add_widget(chk);
            c.add_widget(_make_thumbnail(b.thumbnail_url))
            c.add_widget(_info_col(b.name, f'Vol. {b.number}', b.size))
            btns = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(76), spacing=dp(4))
            btns.add_widget(_make_btn('LEGGI', C_GOLD, callback=lambda bk=b: self.open_reader(bk)))
            btns.add_widget(_make_btn('SCARICA', C_GREEN, callback=lambda bk=b: self.download_book_single(bk)))
            c.add_widget(btns);
            self.ids.volumes_list.add_widget(c)

    def open_reader(self, b):
        s = App.get_running_app().sm.get_screen('reader')
        s.load_book(b);
        App.get_running_app().sm.current = 'reader'

    def download_book_single(self, b):
        self._start_download([b])

    def go_back(self):
        App.get_running_app().sm.current = 'search'

    def _start_download(self, books):
        self.is_downloading = True;
        self.download_progress = 0;
        self.download_max = len(books)

        def _thread():
            app = App.get_running_app();
            d = _get_save_dir()
            for idx, b in enumerate(books):
                safe = "".join(c for c in b.name if c.isalnum() or c in ' .-_').rstrip()
                app.client.download_book_as_cbz(b, os.path.join(d, f"{safe}.cbz"), lambda c, t: Clock.schedule_once(
                    lambda dt: setattr(self, 'download_status', f'Vol. {idx + 1} pag. {c}/{t}')))
                Clock.schedule_once(lambda dt: setattr(self, 'download_progress', idx + 1))
            Clock.schedule_once(lambda dt: setattr(self, 'is_downloading', False), 0.5)

        threading.Thread(target=_thread, daemon=True).start()


class DownloadsScreen(Screen):
    def on_enter(self):
        self.refresh_list()

    def refresh_list(self):
        self.ids.downloads_list.clear_widgets()
        path = _get_save_dir()
        files = sorted([f for f in os.listdir(path) if f.endswith('.cbz')])
        for i, f in enumerate(files):
            full_path = os.path.join(path, f)
            c = _make_card(dp(90))
            thumb = Image(size_hint_x=None, width=dp(58), allow_stretch=True, keep_ratio=True)
            thumb.texture = _get_local_thumbnail(full_path)
            c.add_widget(thumb)
            c.add_widget(_info_col(f, "File locale", f"{os.path.getsize(full_path) // 1048576} MB"))
            btns = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(80), spacing=dp(4))
            btns.add_widget(_make_btn('LEGGI', C_GOLD, callback=lambda fname=f: self.open_local(fname)))
            btns.add_widget(_make_btn('ELIMINA', C_RED, callback=lambda fname=f: self.delete_local(fname)))
            c.add_widget(btns);
            self.ids.downloads_list.add_widget(c)

    def open_local(self, filename):
        path = os.path.join(_get_save_dir(), filename)
        s = App.get_running_app().sm.get_screen('reader')
        s.load_local_book(path, filename);
        App.get_running_app().sm.current = 'reader'

    def delete_local(self, filename):
        try:
            os.remove(os.path.join(_get_save_dir(), filename)); self.refresh_list()
        except:
            pass

    def go_back(self):
        App.get_running_app().sm.current = 'search'


# --- READER SCREEN (LA PARTE NUOVA) ---

class ReaderScreen(Screen):
    book_title = StringProperty('')
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    show_ui = BooleanProperty(True)
    rtl_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._book = None;
        self._cache = {};
        self._loading = set()
        self._is_local = False;
        self._local_path = ""

    def on_pre_enter(self):
        self.show_ui = True
        self.ids.top_bar.pos_hint = {'top': 1}
        self.ids.bottom_bar.pos_hint = {'y': 0}
        self.reset_zoom()

    def load_book(self, b):
        self._is_local = False;
        self._book = b;
        self._cache.clear();
        self._loading.clear()
        self.book_title = b.name;
        self.total_pages = b.pages_count
        saved = load_history(b.id)
        self.current_page = min(saved, b.pages_count)
        self.ids.page_viewer.clear_page();
        self._load_page(self.current_page)

    def load_local_book(self, path, title):
        self._is_local = True;
        self._local_path = path;
        self._cache.clear()
        self.book_title = title
        with zipfile.ZipFile(path, 'r') as z:
            self.total_pages = len([f for f in z.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        saved = load_history(title)
        self.current_page = min(saved, self.total_pages)
        self.ids.page_viewer.clear_page();
        self._load_page(self.current_page)

    def on_left_tap(self):
        if self.rtl_mode:
            self.next_page()
        else:
            self.prev_page()

    def on_right_tap(self):
        if self.rtl_mode:
            self.prev_page()
        else:
            self.next_page()

    def toggle_ui(self):
        self.show_ui = not self.show_ui
        d, t = 0.2, 'out_quad'
        if self.show_ui:
            Animation(pos_hint={'top': 1}, d=d, t=t).start(self.ids.top_bar)
            Animation(pos_hint={'y': 0}, d=d, t=t).start(self.ids.bottom_bar)
        else:
            Animation(pos_hint={'top': 1.2}, d=d, t=t).start(self.ids.top_bar)
            Animation(pos_hint={'y': -0.3}, d=d, t=t).start(self.ids.bottom_bar)

    def jump_to_page(self, page_number):
        p = int(page_number)
        if p != self.current_page and 1 <= p <= self.total_pages:
            self.current_page = p;
            self._load_page(p)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1;
            self._load_page(self.current_page);
            self._save_hist()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1;
            self._load_page(self.current_page);
            self._save_hist()

    def _save_hist(self):
        key = self._book.id if not self._is_local else self.book_title
        save_history(key, self.current_page)

    def reset_zoom(self):
        Animation(scale=1.0, pos=(0, 0), d=0.2).start(self.ids.scatter)

    def check_bounds(self):
        s = self.ids.scatter
        if s.scale <= 1.01: return
        mx = (s.width * s.scale - s.width) / 2
        my = (s.height * s.scale - s.height) / 2
        if s.x > mx: s.x = mx
        if s.x < -mx: s.x = -mx
        if s.y > my: s.y = my
        if s.y < -my: s.y = -my

    def toggle_rtl(self):
        self.rtl_mode = not self.rtl_mode

    def close_reader(self):
        self._save_hist();
        self._cache.clear()
        App.get_running_app().sm.current = 'downloads' if self._is_local else 'search'

    def _load_page(self, n):
        if n < 1 or n > self.total_pages: return
        if n in self._cache:
            self.ids.page_viewer.set_texture(self._cache[n]);
            self._prefetch_next(n);
            return
        if self._is_local:
            threading.Thread(target=self._load_local_page, args=(n,), daemon=True).start()
        else:
            if n in self._loading: return
            self._loading.add(n)

            def _fetch():
                d = App.get_running_app().client._download_page(self._book.get_page_url(n))
                if d:
                    def _apply(dt):
                        try:
                            t = CoreImage(io.BytesIO(d), ext='png').texture
                            self._cache[n] = t
                            if self.current_page == n: self.ids.page_viewer.set_texture(t); self._prefetch_next(n)
                        except:
                            pass

                    Clock.schedule_once(_apply)
                self._loading.discard(n)

            threading.Thread(target=_fetch, daemon=True).start()

    def _load_local_page(self, n):
        try:
            with zipfile.ZipFile(self._local_path, 'r') as z:
                imgs = sorted([f for f in z.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
                data = z.read(imgs[n - 1])

                def _apply(dt):
                    t = CoreImage(io.BytesIO(data), ext='png').texture
                    self._cache[n] = t
                    if self.current_page == n: self.ids.page_viewer.set_texture(t)

                Clock.schedule_once(_apply)
        except:
            pass

    def _prefetch_next(self, curr):
        if self._is_local: return
        for p in range(curr + 1, min(curr + 6, self.total_pages + 1)):
            if p not in self._cache and p not in self._loading: self._do_prefetch(p)

    def _do_prefetch(self, n):
        self._loading.add(n)

        def _fetch():
            d = App.get_running_app().client._download_page(self._book.get_page_url(n))
            if d:
                def _cache_it(dt):
                    try:
                        self._cache[n] = CoreImage(io.BytesIO(d), ext='png').texture
                    except:
                        pass

                Clock.schedule_once(_cache_it)
            self._loading.discard(n)

        threading.Thread(target=_fetch, daemon=True).start()