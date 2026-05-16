import flet as ft


class AppColors:
    # Nkiri-TV premium green cinematic palette
    PRIMARY = "#10B981"  # Emerald 500 - rich, premium green
    SECONDARY = "#059669"  # Emerald 600 - deeper green for accents
    SUCCESS = "#34D399"  # Emerald 400 - lighter green for success
    WARNING = "#F59E0B"  # Amber 500
    ERROR = "#EF4444"  # Red 500

    # Dark Mode
    DARK_BG = "#0A0F0D"
    DARK_SURFACE = "#111814"
    DARK_SURFACE_VARIANT = "#1A2320"
    DARK_TEXT = "#F0FDF4"
    DARK_TEXT_DIM = "#A7C4B5"
    DARK_TEXT_MUTED = "#6B8A7A"

    # Light Mode
    LIGHT_BG = "#F0FDF4"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_VARIANT = "#ECFDF5"
    LIGHT_TEXT = "#022C22"
    LIGHT_TEXT_DIM = "#4D7C5F"
    LIGHT_TEXT_MUTED = "#84A98C"

    SPLASH_BG = "#0A0F0D"

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
            surface = page.dark_theme.color_scheme.surface
            return surface and str(surface).lower().startswith(("#0", "#1"))
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
            surface = page.dark_theme.color_scheme.surface
            is_dark = surface and str(surface).lower().startswith(("#0", "#1"))
            return AppColors.DARK_SURFACE_VARIANT if is_dark else AppColors.LIGHT_SURFACE_VARIANT
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
