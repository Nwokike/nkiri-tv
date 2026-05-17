import flet as ft
from core.theme import AppColors
from core.constants import APP_NAME, APP_TAGLINE


def build_splash_view() -> ft.View:
    return ft.View(
        route="/",
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.SURFACE,
                content=ft.Column(
                    [
                        ft.Image(
                            src="icon.png",
                            width=100,
                            height=100,
                            border_radius=20,
                            fit="contain",
                        ),
                        ft.Container(height=16),
                        ft.Text(
                            APP_NAME,
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            APP_TAGLINE,
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=32),
                        ft.ProgressRing(
                            width=24,
                            height=24,
                            stroke_width=3,
                            color=AppColors.PRIMARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
            )
        ],
        padding=0,
    )
