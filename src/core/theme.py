import flet as ft


class AppColors:
    # Nkiri-TV premium blue cinematic palette
    PRIMARY = "#0EA5E9"  # Sky 500 - rich, premium blue
    SECONDARY = "#0284C7"  # Sky 600 - deeper blue for accents
    SUCCESS = "#38BDF8"  # Sky 400 - lighter blue for success
    WARNING = "#F59E0B"  # Amber 500
    ERROR = "#EF4444"  # Red 500

    # Dark Mode
    DARK_BG = "#0A0E14"
    DARK_SURFACE = "#0F1520"
    DARK_SURFACE_VARIANT = "#162030"
    DARK_TEXT = "#F0F7FF"
    DARK_TEXT_DIM = "#A7C4E2"
    DARK_TEXT_MUTED = "#6B8AB5"

    # Light Mode
    LIGHT_BG = "#F0F7FF"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_VARIANT = "#ECF5FF"
    LIGHT_TEXT = "#021828"
    LIGHT_TEXT_DIM = "#4D7CA8"
    LIGHT_TEXT_MUTED = "#84A9CC"

    SPLASH_BG = "#0A0E14"

    WHITE = ft.Colors.WHITE
    BLACK = ft.Colors.BLACK
    TRANSPARENT = ft.Colors.TRANSPARENT

    @staticmethod
    def _is_dark(page: ft.Page) -> bool:
        if page.theme_mode == ft.ThemeMode.LIGHT:
            return False
        if page.theme_mode == ft.ThemeMode.DARK:
            return True
        try:
            return page.platform_brightness == ft.Brightness.DARK
        except Exception:
            return True

    @staticmethod
    def get_glass_bg(page: ft.Page):
        return ft.Colors.with_opacity(
            0.05, ft.Colors.WHITE if AppColors._is_dark(page) else ft.Colors.BLACK
        )

    @staticmethod
    def get_hover_bg(page: ft.Page):
        return ft.Colors.with_opacity(
            0.1, ft.Colors.WHITE if AppColors._is_dark(page) else ft.Colors.BLACK
        )

    @staticmethod
    def get_surface_variant(page: ft.Page):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            return AppColors.LIGHT_SURFACE_VARIANT
        if page.theme_mode == ft.ThemeMode.DARK:
            return AppColors.DARK_SURFACE_VARIANT
        try:
            is_dark = page.platform_brightness == ft.Brightness.DARK
            return (
                AppColors.DARK_SURFACE_VARIANT
                if is_dark
                else AppColors.LIGHT_SURFACE_VARIANT
            )
        except Exception:
            return AppColors.DARK_SURFACE_VARIANT


class AppTheme:
    @staticmethod
    def get_dark_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                secondary=AppColors.SECONDARY,
                surface=AppColors.DARK_BG,
                on_surface=AppColors.DARK_TEXT,
                on_surface_variant=AppColors.DARK_TEXT_DIM,
                error=AppColors.ERROR,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                outline=AppColors.DARK_TEXT_MUTED,
                surface_tint=AppColors.TRANSPARENT,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )

    @staticmethod
    def get_light_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                secondary=AppColors.SECONDARY,
                surface=AppColors.LIGHT_BG,
                on_surface=AppColors.LIGHT_TEXT,
                on_surface_variant=AppColors.LIGHT_TEXT_DIM,
                error=AppColors.ERROR,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                outline=AppColors.LIGHT_TEXT_MUTED,
                surface_tint=AppColors.TRANSPARENT,
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
