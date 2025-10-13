"""
Value Object: URL
Repräsentiert eine validierte URL mit zusätzlicher Funktionalität.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


@dataclass(frozen=True)
class Url:
    """
    Immutable Value Object für URLs.
    Stellt sicher, dass URLs immer valide sind.
    """

    value: str

    def __post_init__(self):
        """Validierung bei Erstellung"""
        if not self.value:
            raise ValueError("URL darf nicht leer sein")

        parsed = urlparse(self.value)

        if not parsed.scheme:
            raise ValueError(f"URL muss ein Schema haben: {self.value}")

        if not parsed.netloc:
            raise ValueError(f"URL muss einen Host haben: {self.value}")

        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"URL muss http oder https verwenden: {self.value}")

    @classmethod
    def from_string(cls, url_string: str) -> 'Url':
        """Factory-Methode zum Erstellen aus String"""
        return cls(value=url_string.strip())

    @classmethod
    def from_parts(cls, scheme: str, host: str, path: str = "",
                   query: Optional[Dict[str, str]] = None) -> 'Url':
        """Factory-Methode zum Erstellen aus Einzelteilen"""
        query_string = urlencode(query) if query else ""
        url = f"{scheme}://{host}{path}"
        if query_string:
            url += f"?{query_string}"
        return cls(value=url)

    def get_scheme(self) -> str:
        """Gibt das URL-Schema zurück (http/https)"""
        return urlparse(self.value).scheme

    def get_host(self) -> str:
        """Gibt den Hostnamen zurück"""
        return urlparse(self.value).netloc

    def get_path(self) -> str:
        """Gibt den Pfad zurück"""
        return urlparse(self.value).path or "/"

    def get_query_params(self) -> Dict[str, list]:
        """Gibt die Query-Parameter als Dictionary zurück"""
        return parse_qs(urlparse(self.value).query)

    def get_base_url(self) -> str:
        """Gibt die Basis-URL ohne Query-Parameter zurück"""
        parsed = urlparse(self.value)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def is_secure(self) -> bool:
        """Prüft ob HTTPS verwendet wird"""
        return self.get_scheme() == "https"

    def with_path(self, path: str) -> 'Url':
        """Gibt eine neue URL mit geändertem Pfad zurück"""
        parsed = urlparse(self.value)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return Url(value=new_url)

    def with_query_params(self, params: Dict[str, str]) -> 'Url':
        """Gibt eine neue URL mit zusätzlichen Query-Parametern zurück"""
        parsed = urlparse(self.value)
        existing_params = parse_qs(parsed.query)

        # Merge parameters
        for key, value in params.items():
            existing_params[key] = [value]

        new_query = urlencode(existing_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        return Url(value=new_url)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        """Gleichheit basierend auf dem Wert"""
        if not isinstance(other, Url):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
