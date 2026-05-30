import flet as ft
from core.state import state, Episode
from core.theme import AppColors
from core.focus_manager import make_focusable_button, make_focusable_border
from core.constants import (
    LBL_EPISODES,
    LBL_DOWNLOAD_LINKS,
    LBL_EPISODE,
    LBL_SEASON,
    LBL_PAGE,
    LBL_PREVIOUS,
    LBL_NEXT,
)


def build_content_detail_view(
    page_obj: ft.Page,
    series,
    on_load_episodes,
    on_play_episode,
) -> ft.View:
    content = series
    is_movie = content and content.content_type == "movie"

    CARD_HEIGHT = 240

    episode_grid = ft.ResponsiveRow(
        spacing=16,
        run_spacing=16,
        margin=24 if is_movie else ft.Margin(0, 0, 0, 0),
    )

    loading_indicator = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4),
        visible=False,
    )

    prev_spinner = ft.ProgressRing(
        color=AppColors.PRIMARY, stroke_width=3, width=20, height=20, visible=False
    )
    next_spinner = ft.ProgressRing(
        color=AppColors.PRIMARY, stroke_width=3, width=20, height=20, visible=False
    )

    def on_hover_ep(e, container):
        if e.data == "true":
            container.scale = 1.08
            container.border = ft.Border.all(4, AppColors.PRIMARY)
            container.shadow = ft.BoxShadow(
                spread_radius=6,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.7, AppColors.PRIMARY),
                offset=ft.Offset(0, 12),
            )
        else:
            container.scale = 1.0
            container.border = ft.Border.all(4, ft.Colors.TRANSPARENT)
            container.shadow = None
        container.update()

    def _build_episode_card(ep: Episode, idx: int) -> ft.Container:
        poster_url = content.poster if content and content.poster else ""

        is_playing = (
            state.current_content_id == content.nkiri_id
            and state.current_episode_index == idx
        )

        if poster_url:
            img = ft.Image(
                src=poster_url,
                fit="cover",
                expand=True,
                opacity=0.5 if is_playing else 1.0,
            )
        else:
            img = ft.Container(
                content=ft.Icon(
                    ft.Icons.MOVIE_ROUNDED, size=48, color=ft.Colors.ON_SURFACE_VARIANT
                ),
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                alignment=ft.Alignment.CENTER,
            )

        gradient = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    ft.Colors.TRANSPARENT,
                    ft.Colors.with_opacity(0.85, ft.Colors.BLACK),
                ],
            ),
            expand=True,
        )

        if is_movie:
            title_text = ft.Text(
                content.title if content else "Movie",
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
                size=14,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
            meta_parts = []
            if ep.size:
                meta_parts.append(ep.size)
            if ep.quality if hasattr(ep, "quality") else False:
                meta_parts.append(ep.quality)
            if not meta_parts:
                meta_parts.append("1080p")
            meta_text = ft.Text(
                " \u2022 ".join(meta_parts),
                color=AppColors.PRIMARY,
                weight=ft.FontWeight.BOLD,
                size=12,
            )
        else:
            title_text = ft.Text(
                f"{LBL_EPISODE} {ep.episode_number}",
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
                size=14,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
            meta_parts = []
            if ep.season and ep.season != "1":
                meta_parts.append(f"{LBL_SEASON}{ep.season}")
            if ep.size:
                meta_parts.append(ep.size)
            if not meta_parts:
                meta_parts.append(f"{LBL_SEASON}{ep.season}")
            meta_text = ft.Text(
                " \u2022 ".join(meta_parts),
                color=AppColors.PRIMARY,
                weight=ft.FontWeight.BOLD,
                size=12,
            )

        play_badge = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.PLAY_CIRCLE_FILL_ROUNDED
                if not is_playing
                else ft.Icons.EQUALIZER_ROUNDED,
                size=48,
                color=AppColors.PRIMARY if is_playing else ft.Colors.WHITE,
            ),
        )

        content_stack = ft.Stack(
            controls=[
                img,
                gradient,
                play_badge,
                ft.Container(
                    padding=12,
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    content=ft.Column(
                        [title_text, meta_text],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=4,
                    ),
                ),
            ],
            expand=True,
        )

        card_inner = ft.Container(
            content=content_stack,
            border_radius=12,
            clip_behavior="antiAlias",
            height=CARD_HEIGHT,
        )

        card_container = ft.Container(
            content=card_inner,
            border=ft.Border.all(4, ft.Colors.TRANSPARENT),
            padding=4,
            border_radius=16,
            animate_scale=300,
            animate=300,
            ink=True,
            key=f"ep_card_{idx}",
            on_click=lambda _, i=idx, c=content: page_obj.run_task(
                on_play_episode, c, i
            ),
        )
        card_container.on_hover = lambda e, ctr=card_container: on_hover_ep(e, ctr)
        card_container.tab_index = idx + 2
        card_container.on_focus = lambda e, ctr=card_container: _on_focus_ep(e, ctr)
        card_container.on_blur = lambda e, ctr=card_container: _on_blur_ep(e, ctr)

        wrapper = ft.Container(
            content=card_container,
            padding=4,
            col={"xs": 6, "sm": 4, "md": 3, "lg": 2, "xl": 2},
        )
        return wrapper

    def _on_focus_ep(e, ctrl):
        ctrl.scale = 1.08
        ctrl.border = ft.Border.all(4, AppColors.PRIMARY)
        ctrl.shadow = ft.BoxShadow(
            spread_radius=6,
            blur_radius=30,
            color=ft.Colors.with_opacity(0.7, AppColors.PRIMARY),
            offset=ft.Offset(0, 12),
        )
        try:
            ctrl.update()
        except Exception:
            pass

    def _on_blur_ep(e, ctrl):
        ctrl.scale = 1.0
        ctrl.border = ft.Border.all(0, ft.Colors.TRANSPARENT)
        ctrl.shadow = None
        try:
            ctrl.update()
        except Exception:
            pass

    def refresh_episodes():
        episode_grid.controls.clear()
        prev_spinner.visible = False
        next_spinner.visible = False
        if state.is_loading:
            loading_indicator.visible = True
        else:
            loading_indicator.visible = False
            for i, ep in enumerate(state.episodes):
                episode_grid.controls.append(_build_episode_card(ep, i))

        if not is_movie:
            prev_btn.content = ft.Row(
                [
                    ft.Icon(
                        ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                        color=ft.Colors.ON_SURFACE
                        if state.episodes_page > 1
                        else ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        LBL_PREVIOUS,
                        color=ft.Colors.ON_SURFACE
                        if state.episodes_page > 1
                        else ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=8,
            )
            prev_btn.disabled = state.episodes_page <= 1
            num_eps = len(state.episodes)
            prev_btn.tab_index = num_eps + 2

            next_btn.content = ft.Row(
                [
                    ft.Text(
                        LBL_NEXT,
                        color=ft.Colors.ON_SURFACE
                        if state.episodes_has_more
                        else ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                        color=ft.Colors.ON_SURFACE
                        if state.episodes_has_more
                        else ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=8,
            )
            next_btn.disabled = not state.episodes_has_more
            next_btn.tab_index = num_eps + 3

            ep_nav = ft.Row(
                controls=[
                    prev_btn,
                    prev_spinner,
                    ft.Text(
                        f"{LBL_PAGE} {state.episodes_page}",
                        color=ft.Colors.ON_SURFACE,
                        weight=ft.FontWeight.W_500,
                    ),
                    next_spinner,
                    next_btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            )
            episodes_section.controls = [
                episodes_header,
                episode_grid,
                ep_nav,
                loading_indicator,
            ]
        else:
            episodes_section.controls = [
                episodes_header,
                episode_grid,
                loading_indicator,
            ]
        page_obj.update()

    def on_next_ep_page(e):
        next_btn.disabled = True
        next_spinner.visible = True
        page_obj.update()
        state.is_loading = True
        state.episodes_page += 1
        page_obj.run_task(on_load_episodes, content.nkiri_id, state.episodes_page)

    def on_prev_ep_page(e):
        if state.episodes_page > 1:
            prev_btn.disabled = True
            prev_spinner.visible = True
            page_obj.update()
            state.is_loading = True
            state.episodes_page -= 1
            page_obj.run_task(on_load_episodes, content.nkiri_id, state.episodes_page)

    def on_back(e):
        back_btn.disabled = True
        page_obj.update()
        if len(page_obj.views) > 1:
            page_obj.views.pop()
            page_obj.update()

    page_obj.refresh_episodes = refresh_episodes

    poster_url = content.poster if content and content.poster else ""

    bg_controls = [
        ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.SURFACE),
        ),
    ]
    if poster_url:
        bg_controls.insert(
            0,
            ft.Image(
                src=poster_url,
                fit="cover",
                expand=True,
                opacity=0.3,
            ),
        )

    bg_container = ft.Stack(
        expand=True,
        controls=bg_controls,
    )

    bg_overlay = ft.Container(expand=True, bgcolor=ft.Colors.TRANSPARENT)

    title_text = ft.Text(
        content.title if content else "Loading...",
        size=36,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.ON_SURFACE,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    info_text = ft.Text(
        "",
        size=14,
        color=ft.Colors.ON_SURFACE_VARIANT,
        weight=ft.FontWeight.W_500,
    )

    if content:
        parts = []
        if content.year:
            parts.append(content.year)
        if content.content_type:
            parts.append(content.content_type.upper())
        if content.rating:
            parts.append(f"\u2605 {content.rating}")
        info_text.value = " \u2022 ".join(parts)

    poster_widget = ft.Container(
        width=200,
        height=300,
        border_radius=16,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
        content=(
            ft.Image(src=poster_url, fit="cover", border_radius=16)
            if poster_url
            else ft.Container(
                content=ft.Icon(
                    ft.Icons.MOVIE_ROUNDED, size=64, color=ft.Colors.ON_SURFACE_VARIANT
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                border_radius=16,
                alignment=ft.Alignment.CENTER,
            )
        ),
    )

    back_btn = ft.Container(
        content=ft.Icon(
            ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, color=ft.Colors.ON_SURFACE
        ),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=on_back,
    )
    back_btn.tab_index = 1
    make_focusable_button(back_btn)

    header = ft.Container(
        padding=ft.Padding.all(32),
        content=ft.Row(
            [
                poster_widget,
                ft.Container(width=32),
                ft.Column(
                    expand=True,
                    controls=[
                        back_btn,
                        ft.Container(height=16),
                        title_text,
                        ft.Container(height=8),
                        info_text,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    )

    episodes_header = ft.Container(
        padding=ft.Padding.only(left=32, right=32, bottom=16),
        content=ft.Text(
            LBL_EPISODES if not is_movie else LBL_DOWNLOAD_LINKS,
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE,
        ),
    )

    episodes_section = ft.Container(
        expand=False,
        padding=ft.Padding.only(left=32, right=32, bottom=32),
        content=ft.Column([episode_grid, loading_indicator], spacing=16),
    )

    scroll_content = ft.Column(
        [
            header,
            episodes_header,
            episodes_section,
        ],
        spacing=0,
        expand=False,
    )

    scrollable = ft.ListView(
        expand=True,
        controls=[scroll_content],
        padding=0,
        spacing=0,
        auto_scroll=True,
    )

    content_stack = ft.Stack(
        [
            bg_container,
            bg_overlay,
            scrollable,
        ],
        expand=True,
    )

    view = ft.View(
        route=f"/content/{content.nkiri_id}",
        controls=[content_stack],
        padding=0,
    )

    prev_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(LBL_PREVIOUS, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=8,
        ),
        padding=ft.Padding(15, 10, 15, 10),
        border_radius=10,
        border=ft.Border.all(1.5, AppColors.PRIMARY),
        ink=True,
        on_click=on_prev_ep_page,
    )
    prev_btn.tab_index = 2
    make_focusable_border(prev_btn)

    next_btn = ft.Container(
        content=ft.Row(
            [
                ft.Text(LBL_NEXT, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Icon(
                    ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=8,
        ),
        padding=ft.Padding(15, 10, 15, 10),
        border_radius=10,
        border=ft.Border.all(1.5, AppColors.PRIMARY),
        ink=True,
        on_click=on_next_ep_page,
    )
    next_btn.tab_index = 3
    make_focusable_border(next_btn)

    refresh_episodes()

    return view
