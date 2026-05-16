import flet as ft


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

    @staticmethod
    def make_scroll_on_focus(scrollable: ft.ListView | ft.Column):
        def _on_focus(e):
            control_key = getattr(e.control, "key", None)
            if control_key and hasattr(scrollable, "scroll_to"):
                try:
                    scrollable.scroll_to(key=control_key, duration=200)
                except Exception:
                    pass
        return _on_focus

    @staticmethod
    def focus_style(control: ft.Container, focused: bool, primary_color: str = "#8B5CF6"):
        if focused:
            control.border = ft.Border.all(2.5, primary_color)
            control.scale = 1.05
        else:
            control.border = ft.Border.all(0.5, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))
            control.scale = 1.0
