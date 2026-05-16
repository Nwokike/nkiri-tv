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

    EP_CARD_HEIGHT = 140

    episode_grid = ft.ResponsiveRow(
        spacing=16,
        run_spacing=16,
    )

    loading_indicator = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4),
        visible=False,
    )

    def on_hover_ep(e, container):
        if e.data == "true":
            container.scale = 1.03
            container.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.25, AppColors.PRIMARY),
                offset=ft.Offset(0, 6),
            )
        else:
            container.scale = 1.0
            container.shadow = None
        container.update()

    def _on_focus_ep(e, ctrl):
        ctrl.scale = 1.03
        ctrl.bgcolor = ft.Colors.with_opacity(0.2, AppColors.PRIMARY)
        try:
            ctrl.update()
        except Exception:
            pass

    def _on_blur_ep(e, ctrl):
        ctrl.scale = 1.0
        ctrl.bgcolor = AppColors.get_glass_bg(page_obj)
        try:
            ctrl.update()
        except Exception:
            pass

    def _style_focusable(control, focused):
        if focused:
            control.bgcolor = ft.Colors.with_opacity(0.1, AppColors.PRIMARY)
            control.border = ft.Border.all(2, AppColors.PRIMARY)
        else:
            control.bgcolor = None
            control.border = ft.Border.all(1.5, AppColors.PRIMARY)
        try:
            control.update()
        except Exception:
            pass

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

    def _build_episode_card(ep: Episode, idx: int) -> ft.Container:
        play_icon = ft.Icon(ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, size=40, color=ft.Colors.WHITE)

        img = ft.Image(
            src=ep.thumbnail if ep.thumbnail else (content.poster if content.poster else ""),
            fit="cover",
            expand=True,
        )

        gradient = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[
                    ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
                    ft.Colors.TRANSPARENT,
                ],
            ),
            expand=True,
        )

        ep_text = ft.Text(
            f"Episode {ep.episode_number}",
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            size=16,
        )

        meta_text = ft.Text(
            f"S{ep.season}" + (f" \u2022 {ep.size}" if ep.size else ""),
            color=ft.Colors.WHITE_70,
            size=12,
        )

        card_content = ft.Stack(
            controls=[
                img,
                gradient,
                ft.Container(
                    padding=16,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Column(
                        [ep_text, meta_text],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                    )
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER_RIGHT,
                    padding=16,
                    content=play_icon,
                )
            ],
            expand=True,
        )

        card_container = ft.Container(
            content=card_content,
            border_radius=12,
            clip_behavior="antiAlias",
            bgcolor=AppColors.get_glass_bg(page_obj),
            animate_scale=300,
            animate=300,
            ink=True,
            height=EP_CARD_HEIGHT,
            key=f"ep_card_{idx}",
            on_click=lambda _, i=idx: page_obj.run_task(on_play_episode, content, i),
            on_hover=lambda e: on_hover_ep(e, card_container),
        )
        card_container.tab_index = idx + 2
        card_container.on_focus = lambda e: _on_focus_ep(e, card_container)
        card_container.on_blur = lambda e: _on_blur_ep(e, card_container)

        wrapper = ft.Container(
            content=card_container,
            col={"xs": 12, "sm": 6, "md": 4, "lg": 4, "xl": 3},
        )
        return wrapper

    def refresh_episodes():
        episode_grid.controls.clear()
        if state.is_loading:
            loading_indicator.visible = True
        else:
            loading_indicator.visible = False
            for i, ep in enumerate(state.episodes):
                episode_grid.controls.append(_build_episode_card(ep, i))

        prev_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, color=ft.Colors.ON_SURFACE if state.episodes_page > 1 else ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text("Previous", color=ft.Colors.ON_SURFACE if state.episodes_page > 1 else ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=8,
            ),
            padding=ft.Padding(15, 10, 15, 10),
            border_radius=10,
            border=ft.Border.all(1.5, AppColors.PRIMARY),
            ink=True,
            on_click=on_prev_ep_page if state.episodes_page > 1 else None,
        )
        num_eps = len(state.episodes)
        prev_btn.tab_index = num_eps + 2
        prev_btn.on_focus = lambda e: _style_focusable(e.control, True)
        prev_btn.on_blur = lambda e: _style_focusable(e.control, False)

        next_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Next", color=ft.Colors.ON_SURFACE if state.episodes_has_more else ft.Colors.ON_SURFACE_VARIANT),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=ft.Colors.ON_SURFACE if state.episodes_has_more else ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=8,
            ),
            padding=ft.Padding(15, 10, 15, 10),
            border_radius=10,
            border=ft.Border.all(1.5, AppColors.PRIMARY),
            ink=True,
            on_click=on_next_ep_page if state.episodes_has_more else None,
        )
        next_btn.tab_index = num_eps + 3
        next_btn.on_focus = lambda e: _style_focusable(e.control, True)
        next_btn.on_blur = lambda e: _style_focusable(e.control, False)

        ep_nav = ft.Row(
            controls=[prev_btn, ft.Text(f"Page {state.episodes_page}", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.W_500), next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        )

        episodes_section.controls = [episodes_header, episode_grid, ep_nav, loading_indicator]
        page_obj.update()

    def on_next_ep_page(e):
        state.is_loading = True
        state.episodes_page += 1
        page_obj.run_task(on_load_episodes, content.nkiri_id, state.episodes_page)

    def on_prev_ep_page(e):
        if state.episodes_page > 1:
            state.is_loading = True
            state.episodes_page -= 1
            page_obj.run_task(on_load_episodes, content.nkiri_id, state.episodes_page)

    def on_back(e):
        if len(page_obj.views) > 1:
            page_obj.views.pop()
            page_obj.update()

    page_obj.refresh_episodes = refresh_episodes

    bg_image_url = content.poster if content and content.poster else ""

    bg_container = ft.Stack(
        expand=True,
        controls=[
            ft.Image(
                src=bg_image_url,
                fit="cover",
                expand=True,
                opacity=0.3,
            ),
            ft.Container(
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.SURFACE),
            ),
        ],
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

    poster = ft.Container(
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
            ft.Image(src=content.poster, fit="cover", border_radius=16)
            if content and content.poster
            else ft.Container(
                content=ft.Icon(ft.Icons.MOVIE_ROUNDED, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                border_radius=16,
                alignment=ft.Alignment.CENTER,
            )
        ),
    )

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
        padding=ft.Padding.all(32),
        content=ft.Row(
            [
                poster,
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
            "Episodes" if content.content_type == "series" else "Download Links",
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

    refresh_episodes()

    return view
