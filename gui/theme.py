import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def _get_settings_file(root_path: Path) -> Path:
    settings_dir = root_path / 'settings'
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / 'settings.json'

def get_saved_theme(root_path: Path) -> str:
    settings_file = _get_settings_file(root_path)
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('theme', 'light')
        except Exception:
            pass
    return 'light'

def save_theme(root_path: Path, theme_name: str) -> None:
    settings_file = _get_settings_file(root_path)
    data = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}
    data['theme'] = theme_name
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def apply_theme(theme_name: str) -> None:
    app_instance = QApplication.instance()
    if app_instance is None:
        return

    app_instance.setStyleSheet("")

    if theme_name == 'dark':
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 32))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(140, 140, 145))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(55, 55, 60))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Light, QColor(75, 75, 80))
        dark_palette.setColor(QPalette.ColorRole.Midlight, QColor(65, 65, 70))
        dark_palette.setColor(QPalette.ColorRole.Mid, QColor(40, 40, 44))
        dark_palette.setColor(QPalette.ColorRole.Dark, QColor(25, 25, 28))
        dark_palette.setColor(QPalette.ColorRole.Shadow, QColor(15, 15, 18))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(120, 120, 125))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 125))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 125))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(38, 38, 40))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(48, 48, 52))
        app_instance.setPalette(dark_palette)
    else:
        light_palette = QPalette()
        light_palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 247))
        light_palette.setColor(QPalette.ColorRole.WindowText, QColor(25, 25, 28))
        light_palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(238, 238, 242))
        light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 225))
        light_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(25, 25, 28))
        light_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(130, 130, 138))
        light_palette.setColor(QPalette.ColorRole.Text, QColor(25, 25, 28))
        light_palette.setColor(QPalette.ColorRole.Button, QColor(232, 232, 236))
        light_palette.setColor(QPalette.ColorRole.ButtonText, QColor(25, 25, 28))
        light_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        light_palette.setColor(QPalette.ColorRole.Light, QColor(255, 255, 255))
        light_palette.setColor(QPalette.ColorRole.Midlight, QColor(240, 240, 244))
        light_palette.setColor(QPalette.ColorRole.Mid, QColor(190, 190, 198))
        light_palette.setColor(QPalette.ColorRole.Dark, QColor(160, 160, 168))
        light_palette.setColor(QPalette.ColorRole.Shadow, QColor(110, 110, 118))
        light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 102, 204))
        light_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(145, 145, 152))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(145, 145, 152))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(145, 145, 152))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(235, 235, 238))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(225, 225, 228))
        app_instance.setPalette(light_palette)

def get_icon_path(root_path: Path, icon_name: str, theme_name: str = None) -> str:
    if theme_name is None:
        theme_name = get_saved_theme(root_path)
    # images/l -> dark theme;
    # images/d -> light theme.
    subfolder = 'l' if theme_name == 'dark' else 'd'
    return str(root_path / f'UI/images/{subfolder}/{icon_name}')


