import flet as ft
from dataclasses import dataclass, field


@dataclass
class Content:
    id: int
    title: str
    poster: str
    year: str
    rating: str
    description: str
    nkiri_id: int
    categories: list[str] = field(default_factory=list)
    content_type: str = ""


@dataclass
class Episode:
    id: int
    title: str
    season: str
    episode_number: int
    thumbnail: str
    downloadwella_url: str
    direct_url: str = ""
    size: str = ""
    date: str = ""


@dataclass
class Source:
    url: str
    quality: str
    size: str = ""


@ft.observable
class AppState:
    is_loading: bool = False
    search_query: str = ""
    search_results: list = None
    latest_releases: list = None
    latest_page: int = 1
    latest_has_more: bool = True
    search_has_more: bool = True
    episodes: list = None
    episodes_has_more: bool = True
    episodes_page: int = 1
    selected_source: Source | None = None
    current_content_id: int = 0
    current_episode_index: int = 0
    player_error: str | None = None
    active_category: str = "TV Series"
    scraper: object | None = None
    cache: object | None = None

    def __init__(self):
        self.search_results = []
        self.latest_releases = []
        self.episodes = []


state = AppState()
