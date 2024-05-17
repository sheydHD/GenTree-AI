# fonts.py
import dearpygui.dearpygui as dpg
import os
import json

DEFAULT_SETTINGS_FILE = "Data/Settings/default_settings.json"
USER_SETTINGS_FILE = "Data/Settings/user_settings.json"


def load_fonts():
    if os.path.exists(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, "r") as file:
            user_settings = json.load(file)
            font_manager_choices = user_settings.get("font_manager", {})
            font_name = font_manager_choices.get("default_font", "Montserrat-SemiBold")
            font_size = font_manager_choices.get("font_size", 20)
    elif os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, "r") as file:
            default_settings = json.load(file)
            font_manager_choices = default_settings.get("font_manager", {})
            font_name = font_manager_choices.get("default_font", "Montserrat-SemiBold")
            font_size = font_manager_choices.get("font_size", 20)
    else:
        font_name = "Montserrat-SemiBold"
        font_size = 20
        default_settings = {
            "font_manager": {"default_font": font_name, "font_size": font_size},
            "style_editor": {"mvStyleVar_FrameRounding": 5},
        }
        os.makedirs("Data/Settings", exist_ok=True)
        with open(DEFAULT_SETTINGS_FILE, "w") as file:
            json.dump(default_settings, file, indent=4)

    font_path = f"Data/Fonts/{font_name}.ttf"
    with dpg.font_registry():
        loaded_font = dpg.add_font(font_path, font_size)
    return loaded_font


def load_font(font_path, font_size):
    if os.path.exists(font_path):
        with dpg.font_registry():
            loaded_font = dpg.add_font(font_path, font_size)
        return loaded_font
    return None


def get_available_fonts():
    fonts_directory = "Data/Fonts"
    font_extensions = [".ttf", ".otf"]
    available_fonts = []

    for root, dirs, files in os.walk(fonts_directory):
        for file in files:
            if any(file.endswith(ext) for ext in font_extensions):
                font_name = os.path.splitext(file)[0]
                available_fonts.append(font_name)

    return available_fonts
