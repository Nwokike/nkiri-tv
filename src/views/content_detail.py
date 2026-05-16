import flet as ft
from core.state import state, Episode
from core.theme import AppColors


def build_content_detail_view(
    page_obj: ft.Page,
    series,
    on_load_episodes,
    on_play_episode,
) -> ft.View:
    content = series

    episodes_list = ft.Column(spacing=8)

    def on_hover_episode(e, container):
        if e.data == "true":
            container.scale = 1.02
            container.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
                offset=ft.Offset(0, 4),
            )
        else:
            container.scale = 1.0
            container.shadow = None
        container.update()

    def build_episode_card(episode: Episode, idx: int):
        play_icon = ft.Icon(
            ft.Icons.PLAY_CIRCLE_ROUNDED,
            color=AppColors.PRIMARY,
            size=36,
        )

        title_text = ft.Text(
            episode.title,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
            size=14,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        meta_text = ft.Text(
            f"S{episode.season} E{episode.episode_number}" + (f" \u2022 {episode.size}" if episode.size else ""),
            color=ft.Colors.ON_SURFACE_VARIANT,
            size=12,
        )

        card = ft.Container(
            content=ft.Row(
                controls=[
                    play_icon,
                    ft.Column(
                        controls=[title_text, meta_text],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=16,
            border_radius=12,
            bgcolor=AppColors.get_surface_variant(page_obj),
            ink=True,
            on_click=lambda _: on_play_episode(content, idx),
            on_hover=lambda e: on_hover_episode(e, card),
        )
        card.tab_index = idx + 10
        return card

    def update_episodes():
        episodes_list.controls.clear()
        for i, ep in enumerate(state.episodes):
            episodes_list.controls.append(build_episode_card(ep, i))

        if state.is_loading and not state.episodes:
            scroll_content.controls = [
                header,
                content_info,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4)
                )
            ]
        else:
            scroll_content.controls = [header, content_info, episodes_header, episodes_list]

        page_obj.update()

    def _on_focus_btn(e):
        e.control.bgcolor = ft.Colors.with_opacity(0.1, AppColors.PRIMARY)
        try:
            e.control.update()
        except Exception:
            pass

    def _on_blur_btn(e):
        e.control.bgcolor = None
        try:
            e.control.update()
        except Exception:
            pass

    def on_back(e):
        if len(page_obj.views) > 1:
            page_obj.views.pop()
            page_obj.update()

    back_btn = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=on_back,
    )
    back_btn.tab_index = 1
    back_btn.on_focus = _on_focus_btn
    back_btn.on_blur = _on_blur_btn

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=8),
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[back_btn, ft.Text(content.title, size=20, weight=ft.FontWeight.BOLD)],
                    spacing=12,
                ),
            ],
        )
    )

    poster_img = ft.Image(
        src=content.poster if content.poster else "https://via.placeholder.com/300x450?text=No+Poster",
        width=120,
        height=180,
        fit="cover",
        border_radius=12,
    )

    description_text = ft.Text(
        content.description,
        color=ft.Colors.ON_SURFACE_VARIANT,
        size=13,
        max_lines=4,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    meta_items = []
    if content.year:
        meta_items.append(ft.Text(content.year, color=AppColors.PRIMARY, weight=ft.FontWeight.BOLD, size=14))
    if content.rating:
        meta_items.append(ft.Text(content.rating, color=ft.Colors.ON_SURFACE_VARIANT, size=13))
    if content.content_type:
        meta_items.append(ft.Text(content.content_type.upper(), color=AppColors.SECONDARY, weight=ft.FontWeight.BOLD, size=12))

    meta_row = ft.Row(
        controls=meta_items,
        spacing=16,
    )

    content_info = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=8, bottom=16),
        content=ft.Row(
            controls=[
                poster_img,
                ft.Container(width=16),
                ft.Column(
                    controls=[meta_row, ft.Container(height=8), description_text],
                    spacing=8,
                    expand=True,
                ),
            ],
        ),
    )

    episodes_header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=8, bottom=8),
        content=ft.Text(
            "Episodes" if content.content_type == "series" else "Download Links",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE,
        ),
    )

    scroll_content = ft.Column(
        controls=[header, content_info, episodes_list],
        expand=False,
        spacing=0,
    )

    scrollable = ft.ListView(
        expand=True,
        controls=[scroll_content],
        padding=0,
        spacing=0,
        auto_scroll=True,
    )

    view = ft.View(
        route=f"/content/{content.nkiri_id}",
        controls=[
            ft.SafeArea(
                ft.Container(
                    content=scrollable,
                    expand=True,
                    bgcolor=ft.Colors.SURFACE,
                ),
                expand=True,
            )
        ],
        padding=0,
    )

    page_obj.refresh_episodes = update_episodes
    update_episodes()

    return view
