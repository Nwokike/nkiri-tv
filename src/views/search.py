import flet as ft
from core.state import state, Content
from core.theme import AppColors


def build_search_view(
    page_obj: ft.Page,
    on_search,
    on_select_content,
    on_back,
) -> ft.View:

    CARD_HEIGHT = 140
    results_grid = ft.ResponsiveRow(
        spacing=16,
        run_spacing=16,
        margin=24,
    )

    def on_hover_card(e, container):
        if e.data == "true":
            container.scale = 1.05
            container.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.3, AppColors.PRIMARY),
                offset=ft.Offset(0, 8),
            )
        else:
            container.scale = 1.0
            container.shadow = None
        container.update()

    def build_card(content: Content, idx: int):
        img = ft.Image(
            src=content.poster if content.poster else "https://via.placeholder.com/300x450?text=No+Poster",
            fit="cover",
            expand=True,
        )

        gradient = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    ft.Colors.TRANSPARENT,
                    ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
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

        meta_text = ft.Text(
            content.year,
            color=AppColors.PRIMARY,
            weight=ft.FontWeight.BOLD,
            size=12,
        )

        content_stack = ft.Stack(
            controls=[
                img,
                gradient,
                ft.Container(
                    padding=12,
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    content=ft.Column(
                        [title_text, meta_text],
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
            on_hover=lambda e: on_hover_card(e, card_container),
        )
        card_container.tab_index = idx + 10
        card_container.on_focus = lambda e: _on_focus_card(e, card_container)
        card_container.on_blur = lambda e: _on_blur_card(e, card_container)

        wrapper = ft.Container(
            content=card_container,
            col={"xs": 6, "sm": 4, "md": 3, "lg": 2, "xl": 2},
        )
        return wrapper

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

    def on_search_submitted(e):
        query = search_field.value.strip()
        if query:
            page_obj.run_task(on_search, query)

    def update_results():
        results_grid.controls.clear()
        for i, r in enumerate(state.search_results):
            results_grid.controls.append(build_card(r, i))

        if state.is_loading and not state.search_results:
            scroll_content.controls = [
                header,
                search_field_container,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.ProgressRing(color=AppColors.PRIMARY, stroke_width=4)
                )
            ]
        elif not state.search_results and not state.is_loading:
            scroll_content.controls = [
                header,
                search_field_container,
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text("Search movies, series, dramas...", color=ft.Colors.ON_SURFACE_VARIANT, size=16)
                )
            ]
        else:
            scroll_content.controls = [header, search_field_container, results_grid]

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

    search_field = ft.TextField(
        hint_text="Search movies, series...",
        expand=True,
        border=ft.InputBorder.OUTLINED,
        border_radius=10,
        on_submit=on_search_submitted,
    )

    search_btn = ft.Container(
        content=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=ft.Colors.WHITE),
        padding=12,
        border_radius=10,
        bgcolor=AppColors.PRIMARY,
        ink=True,
        on_click=lambda _: on_search_submitted(None),
    )

    search_field_container = ft.Container(
        padding=ft.Padding.only(left=24, right=24, top=16, bottom=8),
        content=ft.Row(
            controls=[search_field, search_btn],
            spacing=8,
        ),
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
        padding=ft.Padding.only(left=24, right=24, top=24, bottom=8),
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[back_btn, ft.Text("Search", size=24, weight=ft.FontWeight.BOLD)],
                    spacing=12,
                ),
            ],
        )
    )

    scroll_content = ft.Column(
        controls=[header, results_grid],
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

    page_obj.refresh_search_results = update_results
    update_results()

    return view
