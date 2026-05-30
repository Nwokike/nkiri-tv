import re
import time
import httpx
from bs4 import BeautifulSoup
from core.config import NKIRI_API, CATEGORIES
from core.state import Content, Episode, Source


class NkiriScraper:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._mem_cache: dict = {}
        self._mem_ttl: dict = {}
        self._resolve_cache: dict = {}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
                timeout=15.0,
                follow_redirects=True,
            )
        return self._client

    def _get_mem(self, key: str, ttl: int = 300):
        if key in self._mem_cache and key in self._mem_ttl:
            if time.time() < self._mem_ttl[key]:
                return self._mem_cache[key]
            del self._mem_cache[key]
            del self._mem_ttl[key]
        return None

    def _set_mem(self, key: str, value, ttl: int = 300):
        self._mem_cache[key] = value
        self._mem_ttl[key] = time.time() + ttl

    @staticmethod
    def _clean_title(raw_title: str) -> tuple[str, str, str]:
        raw_text = BeautifulSoup(raw_title, "html.parser").get_text(strip=True)
        lower_raw = raw_text.lower()
        content_type = "series"
        if any(kw in lower_raw for kw in ["movie", "film"]):
            content_type = "movie"
        elif any(
            kw in lower_raw
            for kw in [
                "s01",
                "s02",
                "s03",
                "s04",
                "s05",
                "s06",
                "s07",
                "s08",
                "s09",
                "s10",
                "season",
                "episode",
            ]
        ):
            content_type = "series"
        title = re.sub(r"\s*\|\s*.*$", "", raw_text).strip()
        title = re.sub(r"\s*Download\s*.*$", "", title, flags=re.IGNORECASE).strip()

        year_match = re.search(r"\((\d{4})\)", title)
        year = year_match.group(1) if year_match else ""
        if year:
            title = title.replace(f"({year})", "").strip()
            title = re.sub(r"\s*[-–—]\s*$", "", title).strip()

        return title, year, content_type

    @staticmethod
    def _parse_rating(content_html: str) -> str:
        patterns = [r"IMDb[:\s]*([0-9.]+)", r"Rating[:\s]*([0-9.]+)"]
        for pattern in patterns:
            match = re.search(pattern, content_html, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    @staticmethod
    def _parse_description(content_html: str) -> str:
        soup = BeautifulSoup(content_html, "html.parser")
        for tag in ["p", "div"]:
            for el in soup.find_all(tag):
                text = el.get_text(strip=True)
                if len(text) > 50 and "download" not in text.lower():
                    return text[:300]
        return ""

    def _parse_episodes(self, content_html: str) -> list[Episode]:
        soup = BeautifulSoup(content_html, "html.parser")
        episodes = []

        download_links = soup.find_all("a", href=re.compile(r"downloadwella\.com"))
        fallback = None

        for link in download_links:
            href = link["href"]
            title_text = link.get_text(strip=True)

            if (
                not title_text
                or "download" in title_text.lower()
                or "click" in title_text.lower()
            ):
                filename = href.split("/")[-1]
                title_text = (
                    filename.replace(".html", "")
                    .replace("(THENKIRI.COM)", "")
                    .replace(".", " ")
                    .strip()
                )

            title_text = re.sub(r"\s+", " ", title_text).strip()

            episode_match = re.search(r"[Ss](\d+)[Ee](\d+)", title_text)
            if not episode_match:
                episode_match = re.search(
                    r"[Ss]eason\s*(\d+)\s*[Ee]pisode\s*(\d+)", title_text, re.IGNORECASE
                )
            if not episode_match:
                episode_match = re.search(
                    r"[Ee]pisode\s*(\d+)", title_text, re.IGNORECASE
                )

            if episode_match:
                season = "1"
                ep_num = 0
                if episode_match.lastindex == 2:
                    season = episode_match.group(1)
                    ep_num = int(episode_match.group(2))
                else:
                    ep_num = int(episode_match.group(1))

                size_match = re.search(r"(\d+(?:\.\d+)?\s*[MGK]B)", title_text)
                size = size_match.group(1) if size_match else ""

                episodes.append(
                    Episode(
                        id=len(episodes) + 1,
                        title=title_text or f"Season {season} Episode {ep_num}",
                        season=season,
                        episode_number=ep_num,
                        thumbnail="",
                        downloadwella_url=href,
                        size=size,
                    )
                )
            else:
                if fallback is None:
                    fallback = (href, title_text)

        if not episodes and fallback:
            href, title_text = fallback
            size_match = re.search(r"(\d+(?:\.\d+)?\s*[MGK]B)", title_text)
            size = size_match.group(1) if size_match else ""
            episodes.append(
                Episode(
                    id=1,
                    title=title_text or "Movie",
                    season="1",
                    episode_number=1,
                    thumbnail="",
                    downloadwella_url=href,
                    size=size,
                )
            )

        return episodes

    async def _fetch_posters(
        self, client: httpx.AsyncClient, media_ids: list[int]
    ) -> dict[int, str]:
        if not media_ids:
            return {}
        ids_str = ",".join(str(x) for x in media_ids)
        mr = await client.get(
            f"{NKIRI_API}/media",
            params={"include": ids_str, "per_page": 20, "_fields": "id,source_url"},
        )
        if mr.status_code != 200:
            return {}
        try:
            return {m["id"]: m.get("source_url", "") for m in mr.json()}
        except Exception:
            return {}

    def _posts_to_content(
        self, posts: list[dict], poster_map: dict[int, str]
    ) -> list[Content]:
        results = []
        for post in posts:
            raw_title = post.get("title", {}).get("rendered", "")
            title, year, content_type = self._clean_title(raw_title)
            poster = poster_map.get(post.get("featured_media", 0), "")

            results.append(
                Content(
                    nkiri_id=post.get("id", 0),
                    title=title,
                    poster=poster,
                    year=year,
                    rating="",
                    description="",
                    categories=[],
                    content_type=content_type,
                )
            )
        return results

    async def latest_releases(
        self, page: int = 1, category: str = "TV Series"
    ) -> tuple[list[Content], bool]:
        cache_key = f"latest_{category}_{page}"
        cached = self._get_mem(cache_key, ttl=300)
        if cached:
            return cached

        cat_id = CATEGORIES.get(category, CATEGORIES["TV Series"])

        client = self._get_client()
        resp = await client.get(
            f"{NKIRI_API}/posts",
            params={
                "categories": cat_id,
                "per_page": 12,
                "page": page,
                "orderby": "date",
                "order": "desc",
                "_fields": "id,title,featured_media,date",
            },
        )
        if resp.status_code != 200:
            return [], False

        try:
            posts = resp.json()
        except Exception:
            return [], False

        media_ids = [p["featured_media"] for p in posts if p.get("featured_media")]
        poster_map = await self._fetch_posters(client, media_ids)

        results = self._posts_to_content(posts, poster_map)

        has_more = len(posts) == 12
        result = (results, has_more)
        self._set_mem(cache_key, result, ttl=300)
        return result

    async def search(self, query: str, page: int = 1) -> tuple[list[Content], bool]:
        cache_key = f"search_{query}_{page}"
        cached = self._get_mem(cache_key, ttl=600)
        if cached:
            return cached

        client = self._get_client()
        resp = await client.get(
            f"{NKIRI_API}/posts",
            params={
                "search": query,
                "per_page": 12,
                "page": page,
                "_fields": "id,title,featured_media,date",
            },
        )
        if resp.status_code != 200:
            return [], False

        try:
            posts = resp.json()
        except Exception:
            return [], False

        media_ids = [p["featured_media"] for p in posts if p.get("featured_media")]
        poster_map = await self._fetch_posters(client, media_ids)

        results = self._posts_to_content(posts, poster_map)

        has_more = len(posts) == 12
        result = (results, has_more)
        self._set_mem(cache_key, result, ttl=600)
        return result

    async def episodes(self, nkiri_id: int) -> list[Episode]:
        cache_key = f"episodes_{nkiri_id}"
        cached = self._get_mem(cache_key, ttl=3600)
        if cached:
            return cached

        client = self._get_client()
        resp = await client.get(
            f"{NKIRI_API}/posts/{nkiri_id}",
            params={"_fields": "id,content"},
        )
        if resp.status_code != 200:
            return []

        try:
            post = resp.json()
        except Exception:
            return []

        content_html = post.get("content", {}).get("rendered", "")
        result = self._parse_episodes(content_html)
        self._set_mem(cache_key, result, ttl=3600)
        return result

    async def resolve_episode(self, downloadwella_url: str) -> Source | None:
        if downloadwella_url in self._resolve_cache:
            return self._resolve_cache[downloadwella_url]

        try:
            file_id_match = re.search(
                r"downloadwella\.com/([a-z0-9]+)/", downloadwella_url
            )
            if not file_id_match:
                return None
            file_id = file_id_match.group(1)

            client = self._get_client()
            resp = await client.post(
                "https://downloadwella.com/",
                data={
                    "op": "download2",
                    "id": file_id,
                    "rand": "",
                    "referer": "",
                    "method_free": "",
                    "method_premium": "",
                },
                headers={
                    "Referer": downloadwella_url,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )
            if resp.status_code != 200:
                return None

            direct_match = re.search(
                r'(https://dwbe\d+\.downloadwella\.com/d/[^"]+\.mkv)', resp.text
            )
            if direct_match:
                source = Source(
                    url=direct_match.group(1),
                    quality="1080p",
                    size="",
                )
                self._resolve_cache[downloadwella_url] = source
                return source

            alt_match = re.search(r'(https://[^\s"]+\.mkv[^\s"]*)', resp.text)
            if alt_match:
                source = Source(
                    url=alt_match.group(1),
                    quality="1080p",
                    size="",
                )
                self._resolve_cache[downloadwella_url] = source
                return source

            return None
        except Exception:
            return None

    def clear_cache(self):
        self._mem_cache.clear()
        self._mem_ttl.clear()

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
