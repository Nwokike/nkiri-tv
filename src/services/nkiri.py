import re
import httpx
from bs4 import BeautifulSoup
from core.config import NKIRI_API, CATEGORIES
from core.state import Content, Episode, Source


class NkiriScraper:
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            follow_redirects=True,
            timeout=30,
        )

    @staticmethod
    def _clean_title(raw_title: str) -> tuple[str, str]:
        title = BeautifulSoup(raw_title, "html.parser").get_text(strip=True)
        title = re.sub(r'\s*\|\s*.*$', '', title).strip()
        title = re.sub(r'\s*Download\s*.*$', '', title, flags=re.IGNORECASE).strip()

        content_type = "series"
        lower = title.lower()
        if any(kw in lower for kw in ["movie", "film"]):
            content_type = "movie"
        elif any(kw in lower for kw in ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "season", "episode"]):
            content_type = "series"

        year_match = re.search(r'\((\d{4})\)', title)
        year = year_match.group(1) if year_match else ""

        return title, year, content_type

    @staticmethod
    def _parse_poster(content_html: str, featured_media: list | None = None) -> str:
        if featured_media:
            for media in featured_media:
                if isinstance(media, dict) and media.get("source_url"):
                    return media["source_url"]
        soup = BeautifulSoup(content_html, "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "use-on-site" not in src.lower() and "dramakey" not in src.lower():
                return src
        return ""

    @staticmethod
    def _parse_rating(content_html: str) -> str:
        patterns = [r'IMDb[:\s]*([0-9.]+)', r'Rating[:\s]*([0-9.]+)']
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
        for link in download_links:
            href = link["href"]
            title_text = link.get_text(strip=True)

            if not title_text or "download" in title_text.lower() or "click" in title_text.lower():
                filename = href.split("/")[-1]
                title_text = filename.replace(".html", "").replace("(THENKIRI.COM)", "").replace(".", " ").strip()

            title_text = re.sub(r'\s+', ' ', title_text).strip()

            episode_match = re.search(r'[Ss](\d+)[Ee](\d+)', title_text)
            if not episode_match:
                episode_match = re.search(r'[Ss]eason\s*(\d+)\s*[Ee]pisode\s*(\d+)', title_text, re.IGNORECASE)
            if not episode_match:
                episode_match = re.search(r'[Ee]pisode\s*(\d+)', title_text, re.IGNORECASE)

            season = "1"
            ep_num = 0
            if episode_match:
                if episode_match.lastindex == 2:
                    season = episode_match.group(1)
                    ep_num = int(episode_match.group(2))
                else:
                    ep_num = int(episode_match.group(1))

            if ep_num == 0:
                continue

            size_match = re.search(r'(\d+(?:\.\d+)?\s*[MGK]B)', title_text)
            size = size_match.group(1) if size_match else ""

            episodes.append(Episode(
                id=len(episodes) + 1,
                title=title_text or f"Season {season} Episode {ep_num}",
                season=season,
                episode_number=ep_num,
                thumbnail="",
                downloadwella_url=href,
                size=size,
            ))

        return episodes

    def latest_releases(self, page: int = 1, category: str = "TV Series") -> tuple[list[Content], bool]:
        cat_id = CATEGORIES.get(category, CATEGORIES["TV Series"])
        resp = self.client.get(
            f"{NKIRI_API}/posts",
            params={
                "categories": cat_id,
                "per_page": 10,
                "page": page,
                "orderby": "date",
                "order": "desc",
                "_embed": 1,
            },
        )
        if resp.status_code != 200:
            return [], False

        try:
            posts = resp.json()
        except Exception:
            return [], False

        results = []
        for post in posts:
            content_html = post.get("content", {}).get("rendered", "")
            raw_title = post.get("title", {}).get("rendered", "")
            title, year, content_type = self._clean_title(raw_title)

            featured = post.get("_embedded", {}).get("wp:featuredmedia", [])
            poster = self._parse_poster(content_html, featured)
            rating = self._parse_rating(content_html)
            description = self._parse_description(content_html)

            categories = []
            for cat in post.get("_embedded", {}).get("wp:term", [[]])[0]:
                if isinstance(cat, dict) and cat.get("taxonomy") == "category":
                    categories.append(cat.get("name", ""))

            results.append(Content(
                id=post.get("id", 0),
                title=title,
                poster=poster,
                year=year,
                rating=rating,
                description=description,
                nkiri_id=post.get("id", 0),
                categories=categories,
                content_type=content_type,
            ))

        has_more = len(posts) == 10 and resp.headers.get("X-WP-TotalPages", "1") != str(page)
        return results, has_more

    def search(self, query: str, page: int = 1) -> tuple[list[Content], bool]:
        resp = self.client.get(
            f"{NKIRI_API}/posts",
            params={
                "search": query,
                "per_page": 10,
                "page": page,
                "_embed": 1,
            },
        )
        if resp.status_code != 200:
            return [], False

        try:
            posts = resp.json()
        except Exception:
            return [], False

        results = []
        for post in posts:
            content_html = post.get("content", {}).get("rendered", "")
            raw_title = post.get("title", {}).get("rendered", "")
            title, year, content_type = self._clean_title(raw_title)

            featured = post.get("_embedded", {}).get("wp:featuredmedia", [])
            poster = self._parse_poster(content_html, featured)
            rating = self._parse_rating(content_html)
            description = self._parse_description(content_html)

            results.append(Content(
                id=post.get("id", 0),
                title=title,
                poster=poster,
                year=year,
                rating=rating,
                description=description,
                nkiri_id=post.get("id", 0),
                categories=[],
                content_type=content_type,
            ))

        has_more = len(posts) == 10
        return results, has_more

    def episodes(self, nkiri_id: int) -> list[Episode]:
        resp = self.client.get(f"{NKIRI_API}/posts/{nkiri_id}")
        if resp.status_code != 200:
            return []

        try:
            post = resp.json()
        except Exception:
            return []

        content_html = post.get("content", {}).get("rendered", "")
        return self._parse_episodes(content_html)

    def resolve_episode(self, downloadwella_url: str) -> Source | None:
        try:
            file_id_match = re.search(r'downloadwella\.com/([a-z0-9]+)/', downloadwella_url)
            if not file_id_match:
                return None
            file_id = file_id_match.group(1)

            resp = self.client.post(
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

            direct_match = re.search(r'(https://dwbe\d+\.downloadwella\.com/d/[^"]+\.mkv)', resp.text)
            if direct_match:
                return Source(
                    url=direct_match.group(1),
                    quality="1080p",
                    size="",
                )

            alt_match = re.search(r'(https://[^\s"]+\.mkv[^\s"]*)', resp.text)
            if alt_match:
                return Source(
                    url=alt_match.group(1),
                    quality="1080p",
                    size="",
                )

            return None
        except Exception:
            return None

    def close(self):
        self.client.close()
