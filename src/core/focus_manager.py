import flet as ft
from core.theme import AppColors


PRIMARY_COLOR = AppColors.PRIMARY


class FocusManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self._back_handler = None
        page.on_keyboard_event = self._handle_keyboard

    def set_back_handler(self, handler: callable):
        self._back_handler = handler

    def _handle_keyboard(self, e: ft.KeyboardEvent):
        if e.key in ("Escape", "Go Back", "Browser Back", "Backspace"):
            if self._back_handler:
                self._back_handler()


def apply_focus_scale(control: ft.Container, focused: bool):
    if focused:
        control.scale = 1.05
        control.shadow = ft.BoxShadow(
            spread_radius=2,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, PRIMARY_COLOR),
            offset=ft.Offset(0, 8),
        )
    else:
        control.scale = 1.0
        control.shadow = None
    try:
        control.update()
    except Exception:
        pass


def apply_focus_border(control: ft.Container, focused: bool):
    if focused:
        control.bgcolor = ft.Colors.with_opacity(0.1, PRIMARY_COLOR)
        control.border = ft.Border.all(2, PRIMARY_COLOR)
    else:
        control.bgcolor = None
        control.border = ft.Border.all(1.5, PRIMARY_COLOR)
    try:
        control.update()
    except Exception:
        pass


def apply_focus_btn(control: ft.Container, focused: bool):
    if focused:
        control.bgcolor = ft.Colors.with_opacity(0.1, PRIMARY_COLOR)
    else:
        control.bgcolor = None
    try:
        control.update()
    except Exception:
        pass


def make_focusable_card(control: ft.Container):
    control.on_focus = lambda e: apply_focus_scale(e.control, True)
    control.on_blur = lambda e: apply_focus_scale(e.control, False)


def make_focusable_button(control: ft.Container):
    control.on_focus = lambda e: apply_focus_btn(e.control, True)
    control.on_blur = lambda e: apply_focus_btn(e.control, False)


def make_focusable_border(control: ft.Container):
    control.on_focus = lambda e: apply_focus_border(e.control, True)
    control.on_blur = lambda e: apply_focus_border(e.control, False)
