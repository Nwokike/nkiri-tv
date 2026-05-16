import flet as ft
from dataclasses import dataclass


@dataclass
class Content:
    id: int
    title: str
    poster: str
    year: str
    rating: str
    description: str
    nkiri_id: int
    categories: list[str]
    content_type: str  # "movie" or "series"


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
    size: str


@ft.observable
class AppState:
    is_loading: bool = False
    search_query: str = ""
    search_results: list[Content] = []
    latest_releases: list[Content] = []
    latest_page: int = 1
    latest_has_more: bool = True
    search_has_more: bool = True
    episodes: list[Episode] = []
    episodes_has_more: bool = True
    episodes_page: int = 1
    selected_source: Source | None = None
    current_content_id: int = 0
    current_episode_index: int = 0
    player_error: str | None = None
    active_category: str = "TV Series"

    def __init__(self):
        self.search_results = []
        self.episodes = []


state = AppState()
