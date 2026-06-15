from __future__ import annotations

import threading
import time
from urllib.parse import urlparse

import httpx

from src.utils.logging import setup_logging
from src.utils.url_security import assert_safe_fetch_url

logger = setup_logging()


class HttpClient:
    def __init__(
        self,
        user_agent: str,
        timeout: float = 30.0,
        delay: float = 2.0,
        max_retries: int = 3,
        excluded_domains: list[str] | None = None,
    ) -> None:
        self.delay = delay
        self.max_retries = max_retries
        self.excluded_domains = set(excluded_domains or [])
        self._last_request = 0.0
        self._robots: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self.respect_robots = True
        self.allowed_domains: set[str] = set()
        self.client = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=timeout,
            follow_redirects=True,
        )

    def set_allowed_domains(self, domains: set[str] | frozenset[str]) -> None:
        self.allowed_domains = {d.lower() for d in domains if d}

    def _domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    def _is_excluded(self, url: str) -> bool:
        domain = self._domain(url)
        return any(ex in domain for ex in self.excluded_domains)

    def _load_disallow_paths(self, domain: str, scheme: str) -> list[str]:
        if domain in self._robots:
            return self._robots[domain]
        robots_url = f"{scheme}://{domain}/robots.txt"
        disallows: list[str] = []
        try:
            with self._lock:
                self._throttle()
                resp = self.client.get(robots_url)
                self._last_request = time.monotonic()
            resp.raise_for_status()
            text = resp.text
            in_star_agent = False
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                lower = line.lower()
                if lower.startswith("user-agent:"):
                    agent = line.split(":", 1)[1].strip()
                    in_star_agent = agent == "*"
                elif in_star_agent and lower.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path and "*" not in path and "?" not in path:
                        disallows.append(path)
        except Exception:
            logger.warning("No se pudo leer robots.txt de %s", domain)
        self._robots[domain] = disallows
        return disallows

    def _can_fetch(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urlparse(url)
        disallows = self._load_disallow_paths(parsed.netloc.lower(), parsed.scheme)
        path = parsed.path or "/"
        for disallow in disallows:
            if path.startswith(disallow):
                return False
        return True

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    def get(self, url: str) -> str:
        with self._lock:
            return self._get_unlocked(url)

    def _get_unlocked(self, url: str) -> str:
        if self.allowed_domains:
            url = assert_safe_fetch_url(url, self.allowed_domains)
        if self._is_excluded(url):
            raise ValueError(f"URL excluida (MercadoLibre u otro dominio bloqueado): {url}")
        if not self._can_fetch(url):
            raise PermissionError(f"robots.txt no permite: {url}")

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                resp = self.client.get(url)
                self._last_request = time.monotonic()
                resp.raise_for_status()
                return resp.text
            except Exception as exc:
                last_error = exc
                logger.warning("GET %s intento %s/%s: %s", url, attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(min(0.5 * attempt, 1.5))
        raise RuntimeError(f"Fallo al obtener {url}") from last_error

    def close(self) -> None:
        self.client.close()
