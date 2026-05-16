import flet as ft
from core.state import state, Content
from core.theme import AppColors


def build_search_view(
    page_obj: ft.Page,
    on_search,
    on_select_content,
    on_back,
) -> ft.View:

    CARD_HEIGHT = 280

    search_field = ft.TextField(
        hint_text="Search movies, series...",
        color=ft.Colors.ON_SURFACE,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
        border_color=ft.Colors.TRANSPARENT,
        border_radius=16,
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        content_padding=20,
        text_size=16,
        on_submit=lambda e: page_obj.run_task(on_search, e.data.strip()),
        focused_border_color=AppColors.PRIMARY,
        focused_bgcolor=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
    )

    results_grid = ft.ResponsiveRow(
        spacing=16,
        run_spacing=16,
    )

    def _on_focus_card(e, ctrl):
        ctrl.scale = 1.05
        ctrl.shadow = ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, AppColors.PRIMARY),
            offset=ft.Offset(0, 8),
        )
        try:
            ctrl.update()
        except Exception:
            pass

    def _on_blur_card(e, ctrl):
        ctrl.scale = 1.0
        ctrl.shadow = None
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

    def _build_card(content: Content, idx: int):
        img = ft.Image(
            src=content.poster if content.poster else "",
            fit="cover",
            expand=True,
        )
        if not content.poster:
            img = ft.Container(
                content=ft.Icon(ft.Icons.MOVIE_ROUNDED, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
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
                    ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
                ],
            ),
            expand=True,
        )

        title_text = ft.Text(
            content.title,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            size=14,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        year_text = ft.Text(
            content.year if content.year else "",
            size=12,
            color=ft.Colors.WHITE_70,
        )

        type_text = ft.Text(
            content.content_type.upper() if content.content_type else "",
            size=12,
            color=ft.Colors.WHITE_70,
        )

        content_stack = ft.Stack(
            controls=[
                img,
                gradient,
                ft.Container(
                    padding=12,
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    content=ft.Column(
                        [
                            title_text,
                            ft.Row([year_text, ft.Container(expand=True), type_text], spacing=4),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=4,
                    )
                )
            ],
            expand=True,
        )

        card_container = ft.Container(
            content=content_stack,
            border_radius=12,
            clip_behavior="antiAlias",
            animate_scale=300,
            animate=300,
            ink=True,
            height=CARD_HEIGHT,
            key=f"search_card_{idx}",
            on_click=lambda _: on_select_content(content),
        )
        card_container.tab_index = idx + 2
        card_container.on_focus = lambda e: _on_focus_card(e, card_container)
        card_container.on_blur = lambda e: _on_blur_card(e, card_container)

        wrapper = ft.Container(
            content=card_container,
            col={"xs": 6, "sm": 4, "md": 3, "lg": 3, "xl": 2},
        )
        return wrapper

    def refresh_results():
        results_grid.controls.clear()
        if state.is_loading:
            loading_indicator.visible = True
            empty_state.visible = False
        elif not state.search_results and state.search_query:
            loading_indicator.visible = False
            empty_state.visible = True
            empty_state.controls[1].value = f"No results found for '{state.search_query}'"
        else:
            loading_indicator.visible = False
            empty_state.visible = False
            for i, c in enumerate(state.search_results):
                results_grid.controls.append(_build_card(c, i))
        page_obj.update()

    page_obj.refresh_search_results = refresh_results

    loading_indicator = ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4),
        visible=False,
    )

    empty_state = ft.Column(
        [
            ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text("Search for movies, series, dramas...", size=16, color=ft.Colors.ON_SURFACE_VARIANT),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )

    back_btn = ft.Container(
        content=ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, color=ft.Colors.ON_SURFACE),
        padding=10,
        border_radius=10,
        ink=True,
        on_click=lambda _: on_back(),
    )
    back_btn.tab_index = 1
    back_btn.on_focus = _on_focus_btn
    back_btn.on_blur = _on_blur_btn

    header = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=16),
        content=ft.Column(
            [
                ft.Row(
                    [
                        back_btn,
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=10,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Image(
                                src="icon.png",
                                width=24,
                                height=24,
                                fit="contain"
                            ),
                        ),
                        ft.Text("Search", size=24, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=12,
                ),
                ft.Container(height=8),
                search_field,
            ],
            spacing=0,
        )
    )

    grid_area = ft.Container(
        expand=True,
        padding=ft.Padding.only(left=24, right=24, bottom=24),
        content=ft.Stack([results_grid, loading_indicator, empty_state]),
    )

    scroll_content = ft.Column(
        [
            header,
            grid_area,
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

    view = ft.View(
        route="/search",
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

    refresh_results()

    return view
