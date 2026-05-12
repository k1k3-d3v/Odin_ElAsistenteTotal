"""
title: Los Ojos de Odín (Lector Web y YouTube)
description: Herramienta de lectura pura. Rastrea webs (Crawl4AI) y extrae transcripciones de YouTube. No guarda datos, solo lee.
author: Quique & Gemini
version: 2.0.0
requirements: aiohttp, loguru, crawl4ai, orjson, tiktoken, youtube-transcript-api, requests
"""

import traceback
import requests
import orjson
import tiktoken
import aiohttp
import asyncio
import re
from urllib.parse import parse_qs, urlparse, quote
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Union, Callable, Literal, Dict
from loguru import logger

# --- CRAWL4AI IMPORTS ---
from crawl4ai import (
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    DefaultTableExtraction,
    LLMConfig,
    LLMExtractionStrategy,
)
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# --- YOUTUBE IMPORTS ---
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)

# OpenWebUI imports for native search
try:
    from open_webui.main import Request, app  # type: ignore
    from open_webui.models.users import UserModel, Users  # type: ignore
    from open_webui.routers.retrieval import SearchForm, process_web_search  # type: ignore

    NATIVE_SEARCH_AVAILABLE = True
except ImportError:
    NATIVE_SEARCH_AVAILABLE = False
    logger.warning("OpenWebUI native search not available.")


class ArticleData(BaseModel):
    topic: str
    summary: str


# --- YOUTUBE HELPER FUNCTIONS ---
YOUTUBE_ID_REGEX = re.compile(
    r"(?:v=|youtu\.be/|youtube\.com/embed/|shorts/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url_or_id: str) -> str:
    candidate = url_or_id.strip()
    if len(candidate) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate
    match = YOUTUBE_ID_REGEX.search(candidate)
    if not match:
        raise ValueError("No se pudo extraer el ID del video de YouTube.")
    return match.group(1)


def _fetch_youtube_transcript_structured(
    url_or_id: str, language: str = "es", fallback_languages: Optional[List[str]] = None
) -> Dict[str, object]:
    if fallback_languages is None:
        fallback_languages = [language, "en", "vi"]
    else:
        if language not in fallback_languages:
            fallback_languages = [language] + fallback_languages

    video_id = extract_video_id(url_or_id)
    last_error: Optional[Exception] = None
    transcript_data = None
    used_language = None

    ytt_api = YouTubeTranscriptApi()

    for lang in fallback_languages:
        try:
            transcript_data = ytt_api.fetch(video_id, languages=[lang])
            used_language = lang
            break
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            last_error = e
            continue

    if transcript_data is None:
        raise RuntimeError(f"No hay transcripción disponible. Razón: {last_error}")

    segments = [
        {"start": getattr(s, "start", None), "text": getattr(s, "text", "")}
        for s in transcript_data
    ]
    full_text = "\n".join(seg["text"] for seg in segments if seg["text"])

    return {"video_id": video_id, "language": used_language, "full_text": full_text}


class Tools:
    class Valves(BaseModel):
        # --- CRAWL4AI VALVES ---
        USE_NATIVE_SEARCH: bool = Field(default=True)
        SEARCH_WITH_SEARXNG: bool = Field(default=False)
        SEARXNG_BASE_URL: str = Field(
            default="http://searxng:8888/search?format=json&q=<query>"
        )
        SEARXNG_API_TOKEN: str = Field(default="")
        SEARXNG_METHOD: Literal["GET", "POST"] = Field(default="GET")
        SEARXNG_TIMEOUT: int = Field(default=30)
        SEARXNG_MAX_RESULTS: int = Field(default=10)

        CRAWL4AI_BASE_URL: str = Field(default="http://crawl4ai:11235")
        CRAWL4AI_USER_AGENT: str = Field(
            default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        CRAWL4AI_TIMEOUT: int = Field(default=60)
        CRAWL4AI_BATCH: int = Field(default=5)
        CRAWL4AI_MAX_URLS: int = Field(default=20)
        CRAWL4AI_EXTERNAL_DOMAINS: bool = Field(default=False)
        CRAWL4AI_EXCLUDE_DOMAINS: str = Field(default="")
        CRAWL4AI_EXCLUDE_SOCIAL_MEDIA_DOMAINS: str = Field(
            default="facebook.com,twitter.com,x.com,linkedin.com,instagram.com,tiktok.com"
        )
        CRAWL4AI_EXCLUDE_IMAGES: Literal["None", "External", "All"] = Field(
            default="None"
        )
        CRAWL4AI_WORD_COUNT_THRESHOLD: int = Field(default=200)
        CRAWL4AI_TEXT_ONLY: bool = Field(default=False)
        CRAWL4AI_DISPLAY_MEDIA: bool = Field(default=True)
        CRAWL4AI_MAX_MEDIA_ITEMS: int = Field(default=5)
        CRAWL4AI_DISPLAY_THUMBNAILS: bool = Field(default=False)
        CRAWL4AI_THUMBNAIL_SIZE: int = Field(default=200)
        CRAWL4AI_VALIDATE_IMAGES: bool = Field(default=True)
        CRAWL4AI_MAX_TOKENS: int = Field(default=0)

        LLM_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
        LLM_API_TOKEN: str = Field(default="")
        LLM_PROVIDER: str = Field(default="openrouter/@preset/default")
        LLM_TEMPERATURE: float = Field(default=0.3)
        LLM_INSTRUCTION: str = Field(
            default="Extract core content. Format output as clean markdown."
        )
        LLM_MAX_TOKENS: int = Field(default=4096)
        MORE_STATUS: bool = Field(default=False)
        DEBUG: bool = Field(default=False)

    class UserValves(BaseModel):
        TRANSCRIPT_LANGUAGE: str = Field(default="es,en")
        CRAWL4AI_MAX_URLS: int = Field(default=None)
        CRAWL4AI_DISPLAY_MEDIA: bool = Field(default=None)
        RESEARCH_MODE: bool = Field(default=False)
        RESEARCH_CRAWL_MODE: Literal[
            "pseudo_adaptive", "llm_guided", "bfs_deep", "research_filter"
        ] = Field(default="pseudo_adaptive")
        RESEARCH_MAX_DEPTH: int = Field(default=2)
        RESEARCH_MAX_PAGES: int = Field(default=15)
        RESEARCH_BATCH_SIZE: int = Field(default=5)
        RESEARCH_INCLUDE_EXTERNAL: bool = Field(default=False)

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()

    async def _emit_status(
        self, emitter: Callable[[dict], Any], description: str, done: bool = False
    ):
        """Función auxiliar oculta a Open WebUI gracias al guion bajo."""
        if emitter:
            await emitter(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "description": description,
                        "done": done,
                    },
                }
            )

    # ====================================================================
    # HERRAMIENTA 1: YOUTUBE TRANSCRIPT
    # ====================================================================
    async def get_youtube_transcript(
        self,
        url: str,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: dict = {},
    ) -> str:
        """
        Extrae todo el texto de un video de YouTube.
        Úsalo SIEMPRE que Quique te pase un enlace de YouTube y pida un resumen o analizar el video.

        :param url: URL completa del video de YouTube.
        """
        try:
            await self._emit_status(
                __event_emitter__, f"Buscando subtítulos para: {url}"
            )
            languages = [
                l.strip()
                for l in self.user_valves.TRANSCRIPT_LANGUAGE.split(",")
                if l.strip()
            ] or ["es", "en"]

            data = await asyncio.to_thread(
                _fetch_youtube_transcript_structured, url, languages[0], languages
            )

            transcript_text = data.get("full_text", "")
            if not transcript_text:
                raise RuntimeError("La transcripción está vacía.")

            await self._emit_status(
                __event_emitter__, "Transcripción obtenida con éxito.", True
            )
            return transcript_text
        except Exception as e:
            await self._emit_status(__event_emitter__, f"Error YouTube: {str(e)}", True)
            return f"Error extrayendo video: {str(e)}"

    # ====================================================================
    # HERRAMIENTA 2: BUSCAR Y RASTREAR WEBS (CRAWL4AI)
    # ====================================================================
    async def search_and_crawl_web(
        self,
        query: str = "",
        url_especifica: str = "",
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Lee el contenido de páginas web o busca información en internet.
        Úsalo cuando Quique te pase un enlace web (que no sea YouTube) para leer, resumir, o cuando necesites investigar en internet.

        :param query: Término de búsqueda (si necesitas buscar algo en internet). Déjalo vacío si pasas una URL.
        :param url_especifica: URL exacta de la página que quieres leer. Déjalo vacío si estás haciendo una búsqueda por query.
        """
        urls_to_crawl = [url_especifica] if url_especifica else []

        await self._emit_status(__event_emitter__, "Iniciando escaneo de la red...")

        if query and not url_especifica:
            if self.valves.SEARCH_WITH_SEARXNG:
                try:
                    search_url = self.valves.SEARXNG_BASE_URL.replace(
                        "<query>", quote(query)
                    )
                    resp = await asyncio.to_thread(requests.get, search_url, timeout=15)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        urls_to_crawl.extend([r["url"] for r in results[:3]])
                except Exception as e:
                    logger.error(f"SearXNG Error: {e}")

        if not urls_to_crawl:
            return "No se ha proporcionado ninguna URL válida y la búsqueda no devolvió resultados."

        await self._emit_status(
            __event_emitter__, f"Crawleando {len(urls_to_crawl)} URLs..."
        )

        headers = {"Content-Type": "application/json"}
        endpoint = f"{self.valves.CRAWL4AI_BASE_URL}/crawl"

        crawler_config = CrawlerRunConfig(
            exclude_external_links=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=self.valves.CRAWL4AI_TIMEOUT * 1000,
        )

        payload = {"urls": urls_to_crawl, "crawler_config": crawler_config.dump()}

        try:
            response = await asyncio.to_thread(
                requests.post,
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.valves.CRAWL4AI_TIMEOUT + 10,
            )
            response.raise_for_status()
            data = response.json()

            resultados = []
            for item in data.get("results", []):
                if item.get("success"):
                    markdown = item.get("markdown", "")
                    url_crawled = item.get("url", "")
                    resultados.append(
                        f"--- CONTENIDO DE {url_crawled} ---\n{markdown[:8000]}"
                    )

            await self._emit_status(
                __event_emitter__, "Contenido extraído correctamente.", True
            )
            return "\n\n".join(resultados)

        except Exception as e:
            await self._emit_status(__event_emitter__, f"Fallo al crawlear: {e}", True)
            return f"Error contactando a Crawl4AI: {str(e)}"
