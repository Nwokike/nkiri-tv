import flet as ft
import asyncio
import base64
import urllib.parse

from core.theme import AppTheme, AppColors
from core.state import state, Content
from core.config import USE_EXTERNAL_PLAYER, KTV_PLAY_STORE_URL, KTV_UPTODOWN_URL, KTV_DEEP_LINK_SCHEME, EXTERNAL_PLAYER_NAMES, DEFAULT_CATEGORY
from core.focus_manager import FocusManager
from services.nkiri import NkiriScraper
from services.cache import Cache
from views.splash import build_splash_view
from views.home import build_home_view
from views.search import build_search_view
from views.content_detail import build_content_detail_view
from views.player import build_player_view


def _theme_button_style(page: ft.Page, is_primary: bool = False):
    return ft.ButtonStyle(
        bgcolor={
            ft.ControlState.FOCUSED: AppColors.PRIMARY,
            ft.ControlState.DEFAULT: AppColors.PRIMARY if is_primary else ft.Colors.SURFACE,
        },
        color={
            ft.ControlState.FOCUSED: ft.Colors.WHITE,
            ft.ControlState.DEFAULT: ft.Colors.WHITE if is_primary else ft.Colors.ON_SURFACE,
        },
    )


def show_ktv_install_dialog(page: ft.Page):
    def open_store(e):
        page.run_task(page.launch_url, KTV_PLAY_STORE_URL)

    def open_uptodown(e):
        page.run_task(page.launch_url, KTV_UPTODOWN_URL)

    def dismiss(e):
        try:
            page.pop_dialog()
        except Exception:
            pass

    player_buttons = []
    for name in EXTERNAL_PLAYER_NAMES:
        player_buttons.append(
            ft.Button(
                content=ft.Text(name),
                icon=ft.Icons.PLAY_CIRCLE_ROUNDED,
                on_click=open_store,
                style=_theme_button_style(page, is_primary=(name == "KTV Player")),
            )
        )

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Install a Player", weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.Text(
                    "To stream this episode, please install one of the following players. "
                    "We recommend KTV Player for the best experience.",
                    size=14,
                ),
                ft.Container(height=16),
                ft.Column(player_buttons, spacing=10),
            ],
            tight=True,
        ),
        actions=[
            ft.Button(content=ft.Text("Not now"), on_click=dismiss),
            ft.Button(content=ft.Text("Download from Uptodown"), on_click=open_uptodown),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.show_dialog(dlg)


async def main(page: ft.Page):
    page.title = "Nkiri TV"
    page.padding = 0
    page.spacing = 0

    def global_error_handler(e):
        page.snack_bar = ft.SnackBar(
            ft.Text("Network error or stream unavailable."),
            bgcolor=AppColors.ERROR,
        )
        page.snack_bar.open = True
        page.update()

    page.on_error = global_error_handler

    page.fonts = {
        "Outfit": "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap"
    }
    page.theme = AppTheme.get_light_theme()
    page.dark_theme = AppTheme.get_dark_theme()
    page.theme.font_family = "Outfit"
    page.dark_theme.font_family = "Outfit"
    page.theme_mode = ft.ThemeMode.SYSTEM

    scraper = NkiriScraper()
    cache = Cache()

    focus_manager = FocusManager(page)

    state.scraper = scraper
    state.cache = cache
    state.active_category = DEFAULT_CATEGORY

    _loading_tasks = {}

    def handle_global_back():
        if len(page.views) > 1:
            top_view = page.views[-1]
            route = getattr(top_view, "route", "")

            if route.startswith("/play"):
                page.run_task(navigate, "/content/" + str(state.current_content_id))
            elif route.startswith("/content"):
                page.run_task(navigate, "/home")
            elif route == "/search":
                page.run_task(navigate, "/home")
            else:
                page.run_task(navigate, "/home")

    focus_manager.set_back_handler(handle_global_back)

    async def navigate(route: str):
        await page.push_route(route)

    async def load_latest(page_num: int = 1):
        task_key = f"latest_{page_num}"
        if task_key in _loading_tasks:
            return
        _loading_tasks[task_key] = True

        state.is_loading = True
        state.latest_page = page_num
        if hasattr(page, "update_home_grid"):
            page.update_home_grid()
        else:
            page.update()

        results, has_more = scraper.latest_releases(page_num, state.active_category)
        state.latest_releases = results
        state.latest_has_more = has_more
        state.is_loading = False
        _loading_tasks.pop(task_key, None)
        if hasattr(page, "update_home_grid"):
            page.update_home_grid()
        else:
            page.update()

    async def load_search(query: str):
        task_key = f"search_{query}"
        if task_key in _loading_tasks:
            return
        _loading_tasks[task_key] = True

        state.is_loading = True
        state.search_query = query
        if hasattr(page, "refresh_search_results"):
            page.refresh_search_results()
        else:
            page.update()

        results, has_more = scraper.search(query, 1)
        state.search_results = results
        state.search_has_more = has_more
        state.is_loading = False
        _loading_tasks.pop(task_key, None)
        if hasattr(page, "refresh_search_results"):
            page.refresh_search_results()
        else:
            page.update()

    async def load_episodes(content_id: int, page_num: int = 1):
        task_key = f"episodes_{content_id}_{page_num}"
        if task_key in _loading_tasks:
            return
        _loading_tasks[task_key] = True

        state.is_loading = True
        state.episodes_page = page_num
        if hasattr(page, "refresh_episodes"):
            page.refresh_episodes()
        else:
            page.update()

        episodes = scraper.episodes(content_id)
        state.episodes = episodes
        state.episodes_has_more = False
        state.is_loading = False
        _loading_tasks.pop(task_key, None)
        if hasattr(page, "refresh_episodes"):
            page.refresh_episodes()
        else:
            page.update()

    async def play_episode(content: Content, episode_index: int):
        state.is_loading = True
        if hasattr(page, "update_home_grid"):
            page.update_home_grid()
        page.update()

        episode = state.episodes[episode_index]

        source = scraper.resolve_episode(episode.downloadwella_url)
        state.is_loading = False

        if not source:
            page.snack_bar = ft.SnackBar(ft.Text("Could not resolve stream."), bgcolor=AppColors.ERROR)
            page.snack_bar.open = True
            page.update()
            return

        state.selected_source = source
        state.current_content_id = content.nkiri_id
        state.current_episode_index = episode_index

        if USE_EXTERNAL_PLAYER:
            page.run_task(play_episode_external, source.url)
        else:
            await navigate("/play")

    async def play_episode_external(mkv_url: str):
        encoded_url = base64.urlsafe_b64encode(mkv_url.encode()).decode()
        deep_link = f"{KTV_DEEP_LINK_SCHEME}{encoded_url}"

        try:
            await page.launch_url(deep_link)
        except Exception:
            pass

        show_ktv_install_dialog(page)

    async def splash_complete():
        await asyncio.sleep(1.5)
        await navigate("/home")

    async def route_change(e: ft.RouteChangeEvent | None = None):
        route = page.route
        parsed = urllib.parse.urlparse(route)

        if parsed.path in ["/", "/home", "/search"]:
            page.views.clear()

        if parsed.path == "/":
            page.views.append(build_splash_view())
            page.run_task(splash_complete)

        elif parsed.path == "/home":
            page.views.append(
                build_home_view(
                    page_obj=page,
                    on_load_latest=load_latest,
                    on_select_content=lambda c: page.run_task(navigate, f"/content/{c.nkiri_id}"),
                    on_search_click=lambda: page.run_task(navigate, "/search"),
                )
            )

        elif parsed.path == "/search":
            page.views.append(
                build_search_view(
                    page_obj=page,
                    on_search=load_search,
                    on_select_content=lambda c: page.run_task(navigate, f"/content/{c.nkiri_id}"),
                    on_back=lambda: page.run_task(navigate, "/home"),
                )
            )

        elif parsed.path.startswith("/content/"):
            content_id = int(parsed.path.split("/")[-1])
            matching = [c for c in state.latest_releases if c.nkiri_id == content_id]
            content_obj = matching[0] if matching else Content(
                id=content_id, title="Loading...", poster="", year="", rating="",
                description="", nkiri_id=content_id, categories=[], content_type="",
            )
            state.episodes_page = 1
            page.views.append(
                build_content_detail_view(
                    page_obj=page,
                    series=content_obj,
                    on_load_episodes=load_episodes,
                    on_play_episode=play_episode,
                )
            )
            page.run_task(load_episodes, content_id, 1)

        elif parsed.path == "/play":
            try:
                page.pop_dialog()
            except Exception:
                pass
            if state.selected_source:
                page.views.append(
                    build_player_view(
                        page_obj=page,
                    )
                )
            else:
                await navigate("/home")

        page.update()

    def view_pop(e: ft.ViewPopEvent):
        if len(page.views) > 1:
            top_view = page.views[-1]
            route = getattr(top_view, "route", "")
            if route.startswith("/play"):
                for control in top_view.controls:
                    if hasattr(control, "pause"):
                        try:
                            control.pause()
                        except Exception:
                            pass

            page.views.pop()
            previous_view = page.views[-1]
            page.run_task(navigate, previous_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    await route_change()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
