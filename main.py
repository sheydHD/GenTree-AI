# main.py

import dearpygui.dearpygui as dpg
import os
import json
import threading  # Import threading for the timer
from helper_functions.main_functions.window import setup_window
from helper_functions.main_functions.fonts import load_fonts
from helper_functions.menu_functions.open_settings import load_settings
from helper_functions.create_database import create_database

DEFAULT_SETTINGS_FILE = "Data/Settings/default_settings.json"
USER_SETTINGS_FILE = "Data/Settings/user_settings.json"

def main():
    dpg.create_context()
    create_database()
    dpg.create_viewport(title="GenTree", width=1920, height=1080)
    dpg.setup_dearpygui()

    os.makedirs("Data/Settings", exist_ok=True)

    if not os.path.exists(DEFAULT_SETTINGS_FILE):
        default_settings = {
            "font_manager": {"default_font": "Montserrat-SemiBold", "font_size": 20},
            "style_editor": {"mvStyleVar_FrameRounding": 5},
        }
        with open(DEFAULT_SETTINGS_FILE, "w") as file:
            json.dump(default_settings, file, indent=4)

    load_settings(
        USER_SETTINGS_FILE
        if os.path.exists(USER_SETTINGS_FILE)
        else DEFAULT_SETTINGS_FILE
    )
    font = load_fonts()
    setup_window(font)

    dpg.show_viewport()
    dpg.set_primary_window("Primary Window", True)
    dpg.maximize_viewport()

    # Check if running in CI
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if is_ci:
        # Close the app after 5 seconds
        def close_app():
            print("Closing app automatically in CI environment.")
            dpg.stop_dearpygui()

        threading.Timer(5, close_app).start()

    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
