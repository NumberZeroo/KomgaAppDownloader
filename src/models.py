# src/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Library:
    """Rappresenta una singola libreria di Komga."""
    id: str
    name: str
    root: str
    unavailable: bool
    scan_on_startup: bool
    scan_cbx: bool
    scan_pdf: bool
    import_comic_info_book: bool
    scan_directory_exclusions: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Library':
        """Crea un oggetto Library da un dizionario proveniente dall'API Komga."""
        return Library(
            id=data.get('id', ''),
            name=data.get('name', ''),
            root=data.get('root', ''),
            unavailable=data.get('unavailable', False),
            scan_on_startup=data.get('scanOnStartup', False),
            scan_cbx=data.get('scanCbx', False),
            scan_pdf=data.get('scanPdf', False),
            import_comic_info_book=data.get('importComicInfoBook', False),
            scan_directory_exclusions=data.get('scanDirectoryExclusions', [])
        )

    def __str__(self) -> str:
        """Restituisce una rappresentazione leggibile della libreria."""
        status = "Indisponibile" if self.unavailable else "Disponibile"
        return f"Libreria '{self.name}' (ID: {self.id}) - Stato: {status}"

# In futuro potresti aggiungere qui altre classi come Series, Book, etc.
# @dataclass
# class Series:
#     ...

@dataclass
class Book:
    """Rappresenta un singolo libro (fumetto) di Komga."""
    id: str
    series_id: str
    series_title: str
    name: str
    number: float
    pages_count: int
    size: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Book':
        """Crea un oggetto Book da un dizionario API."""
        # Estrae i dati, anche da sottolivelli come 'media'
        media = data.get('media', {})
        
        return Book(
            id=data.get('id', ''),
            series_id=data.get('seriesId', ''),
            series_title=data.get('seriesTitle', ''),
            name=data.get('name', ''),
            number=data.get('number', 0.0),
            pages_count=media.get('pagesCount', 0),
            size=data.get('size', '0 B')
        )

    @property
    def thumbnail_url(self) -> str:
        """
        Costruisce l'URL per la copertina/thumbnail del libro.
        NOTA: L'URL base dell'API non è qui, verrà aggiunto nel client.
        """
        return f"/api/v1/books/{self.id}/thumbnail"

    @property
    def file_download_url(self) -> str:
        """Costruisce l'URL per il download del file del libro."""
        return f"/api/v1/books/{self.id}/file"

    def get_page_url(self, page_number: int) -> str:
        """Costruisce l'URL per una pagina specifica del libro."""
        return f"/api/v1/books/{self.id}/pages/{page_number}"

    def __str__(self) -> str:
        return f"Book '{self.name}' [Serie: {self.series_title}]"

@dataclass
class Series:
    """Rappresenta una singola Serie di fumetti di Komga."""
    id: str
    library_id: str
    name: str
    books_count: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Series':
        """Crea un oggetto Series da un dizionario API."""
        metadata = data.get('metadata', {})
        return Series(
            id=data.get('id', ''),
            library_id=data.get('libraryId', ''),
            name=data.get('name', ''),
            books_count=data.get('booksCount', 0)
        )

    @property
    def thumbnail_url(self) -> str:
        """Costruisce l'URL per la copertina/thumbnail della serie."""
        return f"/api/v1/series/{self.id}/thumbnail"

    def __str__(self) -> str:
        return f"Serie '{self.name}' ({self.books_count} libri)"