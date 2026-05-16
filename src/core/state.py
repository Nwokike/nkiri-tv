import flet as ft
from dataclasses import dataclass


@dataclass
class Series:
    id: int
    title: str
    poster: str
    year: str
    rating: str
    description: str
    nkiri_id: int  # WordPress post ID
    categories: list[str]


@dataclass
class Episode:
    id: int
    title: str
    season: str
    episode_number: int
    thumbnail: str
    downloadwella_url: str  # URL to downloadwella page
    direct_url: str = ""  # Resolved direct .mkv URL
    size: str = ""
    date: str = ""


@dataclass
class Source:
    url: str  # Direct .mkv URL
    quality: str  # e.g., "720p", "1080p"
    size: str


@ft.observable
class AppState:
    is_loading: bool = False
    search_query: str = ""
    search_results: list[Series] = []
    latest_releases: list[Series] = []
    latest_page: int = 1
    latest_has_more: bool = True
    search_has_more: bool = True
    episodes: list[Episode] = []
    episodes_has_more: bool = True
    selected_source: Source | None = None
    current_series_id: int = 0
    current_episode_index: int = 0
    player_error: str | None = None
    active_category: str = "TV Series"

    def __init__(self):
        self.search_results = []
        self.episodes = []


state = AppState()
