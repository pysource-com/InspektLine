"""Theme definitions for the InspektLine GUI."""


class DarkTheme:
    """Dark theme color definitions."""

    # Background colors
    BG_PRIMARY = "#0a0a0a"
    BG_SECONDARY = "#0f0f0f"
    BG_CARD = "#121212"
    BG_INPUT = "#1a1a1a"
    BG_HOVER = "#2a2a2a"
    BG_PRESSED = "#0a0a0a"

    # Border colors
    BORDER_PRIMARY = "#1a1a1a"
    BORDER_SECONDARY = "#2a2a2a"
    BORDER_ACTIVE = "#0066ff"

    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#999999"
    TEXT_DISABLED = "#666666"

    # Action colors
    PRIMARY = "#0066ff"
    PRIMARY_HOVER = "#0052cc"
    PRIMARY_PRESSED = "#0047b3"

    # Status colors
    SUCCESS = "#00cc00"
    SUCCESS_HOVER = "#00ff00"
    SUCCESS_PRESSED = "#009900"

    ERROR = "#ff0000"
    ERROR_HOVER = "#ff3333"
    ERROR_PRESSED = "#cc0000"

    WARNING = "#ff9900"
    INFO = "#00ccff"

    # Accent colors
    ACCENT_PURPLE = "#cc44ff"
    ACCENT_PURPLE_HOVER = "#dd66ff"

    # Overlay
    OVERLAY_DARK = "rgba(0, 0, 0, 0.7)"

    @classmethod
    def get_main_window_style(cls):
        """Get main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {cls.BG_PRIMARY};
            }}
            QWidget {{
                background-color: {cls.BG_PRIMARY};
                color: {cls.TEXT_PRIMARY};
            }}
        """

