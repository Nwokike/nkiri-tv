import flet as ft
import asyncio
import base64
import urllib.parse

from core.theme import AppTheme, AppColors
from core.state import state, Content
from core.config import (
    KTV_PLAY_STORE_URL,
    KTV_UPTODOWN_URL,
    KTV_DEEP_LINK_SCHEME,
    DEFAULT_CATEGORY,
)
from core.focus_manager import FocusManager
from core.constants import (
    APP_NAME,
    ERR_NETWORK,
    ERR_NO_STREAM,
    ERR_LOAD_EPISODE,
    LBL_INSTALL_PLAYER_TITLE,
    LBL_INSTALL_PLAYER_BODY,
    LBL_NOT_NOW,
    LBL_DOWNLOAD_UPTODOWN,
)
from services.nkiri import NkiriScraper
from services.cache import Cache
from views.home import build_home_view
from views.search import build_search_view
from views.content_detail import build_content_detail_view


def _theme_button_style():
    return ft.ButtonStyle(
        bgcolor={
            ft.ControlState.FOCUSED: AppColors.PRIMARY,
            ft.ControlState.DEFAULT: ft.Colors.SURFACE,
        },
        color={
            ft.ControlState.FOCUSED: ft.Colors.WHITE,
            ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE,
        },
    )


def show_ktv_install_dialog(page: ft.Page):
    page.dialog_open = True

    async def open_store(e):
        page.dialog_open = False
        try:
            page.pop_dialog()
        except Exception:
            pass
        try:
            await asyncio.wait_for(
                ft.UrlLauncher().launch_url(KTV_PLAY_STORE_URL), timeout=1.0
            )
        except Exception:
            pass
        page.update()

    async def open_uptodown(e):
        page.dialog_open = False
        try:
            page.pop_dialog()
        except Exception:
            pass
        try:
            await asyncio.wait_for(
                ft.UrlLauncher().launch_url(KTV_UPTODOWN_URL), timeout=1.0
            )
        except Exception:
            pass
        page.update()

    def dismiss(e):
        page.dialog_open = False
        try:
            page.pop_dialog()
        except Exception:
            pass
        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(LBL_INSTALL_PLAYER_TITLE, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text(LBL_INSTALL_PLAYER_BODY, size=14),
            ],
            tight=True,
        ),
        actions=[
            ft.Button(content=ft.Text(LBL_NOT_NOW), on_click=dismiss),
            ft.Button(
                content=ft.Text("Play Store"),
                on_click=lambda e: page.run_task(open_store, e),
                style=_theme_button_style(),
            ),
            ft.Button(
                content=ft.Text(LBL_DOWNLOAD_UPTODOWN),
                on_click=lambda e: page.run_task(open_uptodown, e),
                style=_theme_button_style(),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.show_dialog(dlg)


class AppController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.scraper: NkiriScraper | None = None
        self.cache: Cache | None = None
        self.focus_manager: FocusManager | None = None
        self._loading_locks: dict[str, asyncio.Lock] = {}

    async def init(self):
        self.page.title = APP_NAME
        self.page.padding = 0
        self.page.spacing = 0

        self.page.on_error = lambda e: self._show_error_snackbar()

        self.page.fonts = {"Outfit": "assets/outfit.css"}
        self.page.theme = AppTheme.get_light_theme()
        self.page.dark_theme = AppTheme.get_dark_theme()
        self.page.theme.font_family = "Outfit"
        self.page.dark_theme.font_family = "Outfit"
        self.page.theme_mode = ft.ThemeMode.SYSTEM

        self.cache = Cache()
        self.scraper = NkiriScraper()

        await self.cache.start_sweep(interval=300)

        state.scraper = self.scraper
        state.cache = self.cache
        state.active_category = DEFAULT_CATEGORY

        self.focus_manager = FocusManager(self.page)
        self.focus_manager.set_back_handler(self._handle_global_back)

    def _show_error_snackbar(self):
        try:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(ERR_NETWORK),
                bgcolor=AppColors.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._loading_locks:
            self._loading_locks[key] = asyncio.Lock()
        return self._loading_locks[key]

    def _handle_global_back(self):
        if getattr(self.page, "dialog_open", False):
            self.page.dialog_open = False
            try:
                self.page.pop_dialog()
            except Exception:
                pass
            self.page.update()
            return
        if len(self.page.views) > 1:
            self.page.views.pop()
            self.page.update()

    async def navigate(self, route: str):
        await self.page.push_route(route)

    async def load_latest(self, page_num: int = 1):
        task_key = f"latest_{page_num}"
        lock = self._get_lock(task_key)
        if lock.locked():
            return

        async with lock:
            state.is_loading = True
            state.latest_page = page_num
            self._update_home_grid()

            try:
                results, has_more = await self.scraper.latest_releases(
                    page_num, state.active_category
                )
                state.latest_releases = results
                state.latest_has_more = has_more
            except Exception:
                state.latest_releases = []
                state.latest_has_more = False
            finally:
                state.is_loading = False
                self._update_home_grid()

    async def load_search(self, query: str):
        if not query:
            return
        task_key = f"search_{query}"
        lock = self._get_lock(task_key)
        if lock.locked():
            return

        async with lock:
            state.is_loading = True
            state.search_query = query
            self._refresh_search_results()

            try:
                results, has_more = await self.scraper.search(query, 1)
                state.search_results = results
                state.search_has_more = has_more
            except Exception:
                state.search_results = []
                state.search_has_more = False
            finally:
                state.is_loading = False
                self._refresh_search_results()

    async def load_episodes(self, content_id: int, page_num: int = 1):
        task_key = f"episodes_{content_id}"
        lock = self._get_lock(task_key)
        if lock.locked():
            return

        async with lock:
            state.is_loading = True
            state.episodes_page = page_num
            self._refresh_episodes()

            try:
                episodes = await self.scraper.episodes(content_id)
                state.episodes = episodes
                state.episodes_has_more = False
            except Exception:
                state.episodes = []
                state.episodes_has_more = False
            finally:
                state.is_loading = False
                self._refresh_episodes()

    async def play_episode(self, content: Content, episode_index: int):
        if not state.episodes:
            self._show_snackbar(ERR_LOAD_EPISODE, AppColors.ERROR)
            return

        self._show_snackbar("Resolving cinematic stream...", AppColors.PRIMARY)

        try:
            episode = state.episodes[episode_index]
            source = await self.scraper.resolve_episode(episode.downloadwella_url)

            if not source:
                self._show_snackbar(ERR_NO_STREAM, AppColors.ERROR)
                return

            state.selected_source = source
            state.current_content_id = content.nkiri_id
            state.current_episode_index = episode_index

            self._refresh_episodes()

            self.page.run_task(self._play_episode_external, source.url)
        except Exception:
            self._show_snackbar(ERR_LOAD_EPISODE, AppColors.ERROR)

    async def _play_episode_external(self, mkv_url: str):
        # Strip trailing '=' padding characters to prevent URL query parameter parsing issues
        encoded_url = base64.urlsafe_b64encode(mkv_url.encode()).decode().rstrip("=")
        deep_link = f"{KTV_DEEP_LINK_SCHEME}{encoded_url}"

        try:
            # We await the launch with a 1.0s timeout. If it succeeds, KTV Player opens,
            # and since the app goes to the background, the completion event is suspended.
            # Thus, TimeoutError is raised, which is actually a SUCCESS indicator!
            # If it fails instantly (e.g. scheme not registered), Exception is raised immediately.
            await asyncio.wait_for(ft.UrlLauncher().launch_url(deep_link), timeout=1.0)
        except asyncio.TimeoutError:
            pass  # Successfully launched and transitioned to background!
        except Exception:
            show_ktv_install_dialog(self.page)

    async def route_change(self, e: ft.RouteChangeEvent | None = None):
        route = self.page.route
        parsed = urllib.parse.urlparse(route)

        if parsed.path in ["/", "/home", "/search"]:
            self.page.views.clear()

        if parsed.path in ["/", "/home"]:
            self.page.views.append(
                build_home_view(
                    page_obj=self.page,
                    on_load_latest=self.load_latest,
                    on_select_content=lambda c: self.page.run_task(
                        self.navigate, f"/content/{c.nkiri_id}"
                    ),
                    on_search_click=lambda _=None: self.page.run_task(
                        self.navigate, "/search"
                    ),
                )
            )

        elif parsed.path == "/search":
            self.page.views.append(
                build_search_view(
                    page_obj=self.page,
                    on_search=self.load_search,
                    on_select_content=lambda c: self.page.run_task(
                        self.navigate, f"/content/{c.nkiri_id}"
                    ),
                    on_back=lambda _=None: self.page.run_task(self.navigate, "/home"),
                )
            )

        elif parsed.path.startswith("/content/"):
            try:
                content_id = int(parsed.path.split("/")[-1])
            except ValueError:
                await self.navigate("/home")
                return

            matching = [c for c in state.latest_releases if c.nkiri_id == content_id]
            if not matching:
                matching = [c for c in state.search_results if c.nkiri_id == content_id]
            content_obj = (
                matching[0]
                if matching
                else Content(
                    nkiri_id=content_id,
                    title="Loading...",
                    poster="",
                    year="",
                    rating="",
                    description="",
                    categories=[],
                    content_type="",
                )
            )
            state.episodes_page = 1
            self.page.views.append(
                build_content_detail_view(
                    page_obj=self.page,
                    series=content_obj,
                    on_load_episodes=self.load_episodes,
                    on_play_episode=self.play_episode,
                )
            )
            self.page.run_task(self.load_episodes, content_id, 1)

        self.page.update()

    def view_pop(self, e: ft.ViewPopEvent):
        if len(self.page.views) > 1:
            self.page.views.pop()
            if self.page.views:
                self.page.route = self.page.views[-1].route
            self.page.update()

    def _update_home_grid(self):
        if hasattr(self.page, "update_home_grid"):
            self.page.update_home_grid()
        else:
            self.page.update()

    def _refresh_search_results(self):
        if hasattr(self.page, "refresh_search_results"):
            self.page.refresh_search_results()
        else:
            self.page.update()

    def _refresh_episodes(self):
        if hasattr(self.page, "refresh_episodes"):
            self.page.refresh_episodes()
        else:
            self.page.update()

    def _show_snackbar(self, message: str, color: str):
        try:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(message),
                bgcolor=color,
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass

    async def cleanup(self):
        if self.scraper:
            await self.scraper.close()
        if self.cache:
            await self.cache.close()


async def main(page: ft.Page):
    controller = AppController(page)
    await controller.init()

    page.on_route_change = controller.route_change
    page.on_view_pop = controller.view_pop

    await controller.route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
