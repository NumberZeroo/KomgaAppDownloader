# src/client.py
import requests
import base64
import json
from typing import List, Optional, Dict, Any, Callable
import tempfile
import zipfile
import shutil
import os
from requests.adapters import HTTPAdapter  #

from .models import Library, Book, Series


class ApiClient:
    def __init__(self, base_url):
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.session = requests.Session()

        # --- OTTIMIZZAZIONE VELOCITÀ ---
        # Creiamo un adapter per gestire pool di connessioni multiple
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # -------------------------------

        self.session.headers.update({
            'User-Agent': 'KomgaDownloaderClient/1.0',
        })

    def login(self, email, password):
        # Assicuriamoci che l'URL sia formattato bene
        if not self.base_url.startswith(('http://', 'https://')):
            return False, "L'URL deve iniziare con http:// o https://"

        login_url = f"{self.base_url}/api/v2/users/me"
        auth_string = f"{email}:{password}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json'  # Chiediamo esplicitamente JSON
        }

        try:
            # Impostiamo un timeout per evitare che l'app si blocchi all'infinito
            # se il server non risponde
            response = self.session.get(login_url, headers=headers, timeout=10)

            # 1. Controlla codici di errore HTTP (401 Unauthorized, 404 Not Found, ecc.)
            response.raise_for_status()

            # 2. Verifica che il contenuto sia effettivamente JSON (caratteristica di Komga)
            data = response.json()

            # 3. Controllo di sicurezza: verifichiamo che ci sia un campo tipico di Komga
            if 'email' in data or 'role' in data:
                return True, None
            else:
                return False, "Il server ha risposto, ma non sembra essere un server Komga."

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Credenziali errate (Email o Password)."
            return False, f"Errore server: {e.response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Impossibile connettersi al server. Controlla l'indirizzo."
        except requests.exceptions.Timeout:
            return False, "Il server ha impiegato troppo tempo a rispondere."
        except Exception as e:
            return False, f"Errore imprevisto: {str(e)}"

    def search_books(self, search_term: str, size: int = 1000) -> List[Book]:
        search_url = f"{self.base_url}/api/v1/books/list"
        params = {'size': size}
        payload = {"fullTextSearch": search_term}
        try:
            response = self.session.post(search_url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return [Book.from_dict(b_data) for b_data in data.get('content', [])]
        except:
            return []

    def search_series(self, search_term: str, size: int = 1000) -> List[Series]:
        search_url = f"{self.base_url}/api/v1/series/list"
        params = {'size': size}
        payload = {"fullTextSearch": search_term}
        try:
            response = self.session.post(search_url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return [Series.from_dict(s_data) for s_data in data.get('content', [])]
        except:
            return []

    def get_book_thumbnail(self, thumbnail_path: str) -> bytes | None:
        url = f"{self.base_url}{thumbnail_path}"
        try:
            return self.session.get(url).content
        except:
            return None

    def _download_page(self, page_url: str) -> bytes | None:
        url = f"{self.base_url}{page_url}"
        try:
            # Chiediamo WebP se possibile, è molto più leggero
            response = self.session.get(url, headers={'Accept': 'image/webp,image/jpeg'})
            response.raise_for_status()
            return response.content
        except:
            return None

    def download_book_as_cbz(self, book: 'Book', save_path: str, progress_callback: Callable):
        temp_dir = tempfile.mkdtemp(prefix="komga_")
        try:
            for i in range(1, book.pages_count + 1):
                data = self._download_page(book.get_page_url(i))
                if data:
                    with open(os.path.join(temp_dir, f"{i:04d}.jpg"), 'wb') as f:
                        f.write(data)
                progress_callback(i, book.pages_count)
            with zipfile.ZipFile(save_path, 'w') as zf:
                for f in sorted(os.listdir(temp_dir)):
                    zf.write(os.path.join(temp_dir, f), arcname=f)
            return True, "Successo"
        except Exception as e:
            return False, str(e)
        finally:
            shutil.rmtree(temp_dir)

    def get_books_for_series(self, series: 'Series') -> List[Book]:
        books_url = f"{self.base_url}/api/v1/books/list"
        params = {'page': 0, 'size': series.books_count, 'sort': 'metadata.numberSort,asc'}
        payload = {"condition": {"allOf": [{"seriesId": {"operator": "is", "value": series.id}}]}}
        try:
            response = self.session.post(books_url, params=params, json=payload)
            data = response.json()
            return [Book.from_dict(b_data) for b_data in data.get('content', [])]
        except:
            return []