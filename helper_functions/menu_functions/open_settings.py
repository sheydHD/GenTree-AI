import dearpygui.dearpygui as dpg
import os
import json
from helper_functions.main_functions.logo import setup_logo
from helper_functions.main_functions.fonts import (
    get_available_fonts,
    load_fonts,
)

DEFAULT_SETTINGS_FILE = "Data/Settings/default_settings.json"
USER_SETTINGS_FILE = "Data/Settings/user_settings.json"

# Create the "Data/Settings" directory if it doesn

os.makedirs("Data/Settings", exist_ok=True)

opened_settings = []

user_choices = {"style_editor": {}, "font_manager": {}}


def open_settings(sender, app_data, user_data):
    # Check if the "Settings" window is already open
    if dpg.does_item_exist("open_settings"):
        # If the window is open, bring it to the front
        dpg.focus_item("open_settings")
    else:
        with dpg.window(
            label="Settings",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag="open_settings",
        ):
            setup_buttons()


def setup_buttons():
    window_width = dpg.get_viewport_width()

    button_width = 200
    button_height = 50
    button_spacing = 10
    start_y = 500

    button_props = {
        "width": button_width,
        "height": button_height,
    }

    buttons = [
        ("Font Settings", Font_Settings),
        ("Style Settings", Style_Settings),
        ("Set Default Settings", Set_Default_Settings),
        ("Cancel and Return", Cancel_And_Return),
    ]

    for i, (label, callback) in enumerate(buttons):
        dpg.add_button(
            label=label,
            callback=callback,
            pos=(
                (window_width - button_width) // 2,
                start_y + i * (button_height + button_spacing),
            ),
            **button_props,
        )


def Font_Settings(sender, app_data, user_data):
    if dpg.does_item_exist("font_settings"):
        dpg.focus_item("font_settings")
    else:
        with dpg.window(
            label="Font Settings",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag="font_settings",
        ):
            dpg.add_text("Select Font:")
            available_fonts = get_available_fonts()
            dpg.add_combo(
                available_fonts,
                default_value=user_choices["font_manager"].get(
                    "default_font", "Montserrat-SemiBold"
                ),
                tag="font_combo",
                callback=lambda s, a: apply_font_settings(),
            )
            dpg.add_text("Select Font Size:")
            dpg.add_slider_int(
                min_value=10,
                max_value=40,
                default_value=user_choices["font_manager"].get("font_size", 20),
                tag="font_size_slider",
                callback=lambda s, a: apply_font_settings(),
            )

            dpg.add_text(
                "", tag="font_info"
            )  # Add a text item to display the information message

            def save_font_settings():
                save_settings(USER_SETTINGS_FILE)
                dpg.delete_item("font_settings")

            def cancel_font_settings():
                load_settings(
                    USER_SETTINGS_FILE
                    if os.path.exists(USER_SETTINGS_FILE)
                    else DEFAULT_SETTINGS_FILE
                )
                dpg.delete_item("font_settings")

            dpg.add_button(label="Save", callback=save_font_settings)
            dpg.add_button(label="Cancel", callback=cancel_font_settings)

            def apply_font_settings():
                selected_font = dpg.get_value("font_combo")
                font_size = dpg.get_value("font_size_slider")

                if selected_font != user_choices["font_manager"].get("default_font"):
                    dpg.set_value(
                        "font_info", "Restart the program to apply font changes."
                    )
                else:
                    dpg.set_value("font_info", "")

                user_choices["font_manager"]["default_font"] = selected_font
                user_choices["font_manager"]["font_size"] = font_size

                # Update the font size instantly
                dpg.set_global_font_scale(font_size / 20)


def Style_Settings(sender, app_data, user_data):
    if dpg.does_item_exist("style_settings"):
        dpg.focus_item("style_settings")
    else:
        with dpg.window(
            label="Style Settings",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag="style_settings",
        ):
            dpg.add_text("Frame Rounding:")
            dpg.add_slider_int(
                min_value=0,
                max_value=12,
                default_value=user_choices["style_editor"].get(
                    "mvStyleVar_FrameRounding", 5
                ),
                tag="frame_rounding_slider",
                callback=lambda s, a: apply_style_settings(),
            )

            def apply_style_settings():
                frame_rounding = dpg.get_value("frame_rounding_slider")
                with dpg.theme() as global_theme:
                    with dpg.theme_component(dpg.mvAll):
                        dpg.add_theme_style(
                            dpg.mvStyleVar_FrameRounding,
                            frame_rounding,
                            category=dpg.mvThemeCat_Core,
                        )
                dpg.bind_theme(global_theme)

            def save_style_settings():
                user_choices["style_editor"]["mvStyleVar_FrameRounding"] = (
                    dpg.get_value("frame_rounding_slider")
                )
                save_settings(USER_SETTINGS_FILE)
                dpg.delete_item("style_settings")

            def cancel_style_settings():
                load_settings(
                    USER_SETTINGS_FILE
                    if os.path.exists(USER_SETTINGS_FILE)
                    else DEFAULT_SETTINGS_FILE
                )
                dpg.delete_item("style_settings")

            dpg.add_button(label="Save", callback=save_style_settings)
            dpg.add_button(label="Cancel", callback=cancel_style_settings)


def Set_Default_Settings(sender, app_data, user_data):
    default_settings = {
        "font_manager": {
            "default_font": "Montserrat-SemiBold",
            "font_size": 20,
        },
        "style_editor": {
            "mvStyleVar_FrameRounding": 5,
        },
    }

    with open(DEFAULT_SETTINGS_FILE, "w") as file:
        json.dump(default_settings, file, indent=4)

    user_choices["font_manager"] = default_settings["font_manager"]
    user_choices["style_editor"] = default_settings["style_editor"]

    save_settings(USER_SETTINGS_FILE)
    load_settings(USER_SETTINGS_FILE)

    # Show a popup with the restart information
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    window_width = 500
    window_height = 110
    window_pos = (
        (viewport_width - window_width) // 2 - 10,
        (viewport_height - window_height) // 2,
    )

    with dpg.window(
        label="Restart Required",
        modal=True,
        no_title_bar=True,
        popup=True,
        tag="restart_popup",
        width=window_width,
        height=window_height,
        pos=window_pos,
        no_resize=True,
        no_move=True,
    ):
        text_width, text_height = dpg.get_text_size(
            "Default settings have been applied."
        )
        dpg.add_text(
            "Default settings have been applied.",
            pos=(
                (window_width - text_width) // 2,
                (window_height - text_height) // 2 - 35,
            ),
        )
        text_width, text_height = dpg.get_text_size(
            "Please restart the program for the changes to take effect."
        )
        dpg.add_text(
            "Please restart the program for the changes to take effect.",
            pos=(
                (window_width - text_width) // 2,
                (window_height - text_height) // 2 - 10,
            ),
        )
        dpg.add_button(
            label="OK",
            width=75,
            pos=((window_width - 75) // 2, window_height - 40),
            callback=lambda: dpg.delete_item("restart_popup"),
        )

    dpg.delete_item("open_settings")


def Save_Settings(sender, app_data, user_data):
    save_settings(USER_SETTINGS_FILE)
    dpg.delete_item("open_settings")


def save_settings(settings_file):
    settings = {
        "font_manager": user_choices["font_manager"],
        "style_editor": user_choices["style_editor"],
    }
    with open(settings_file, "w") as file:
        json.dump(settings, file)
    load_settings(settings_file)


def update_ui_font():
    loaded_font = load_fonts()
    if loaded_font:
        dpg.bind_font(loaded_font)
    font_size = user_choices["font_manager"].get("font_size", 20)
    dpg.set_global_font_scale(font_size / 20)


def load_settings(settings_file):
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as file:
                settings = json.load(file)
                user_choices["font_manager"] = settings.get("font_manager", {})
                user_choices["style_editor"] = settings.get("style_editor", {})
        except json.JSONDecodeError:
            # If the JSON file is empty or invalid, create a new settings file with default values
            default_settings = {
                "font_manager": {
                    "default_font": "Montserrat-SemiBold",
                    "font_size": 20,
                },
                "style_editor": {"mvStyleVar_FrameRounding": 5},
            }
            with open(settings_file, "w") as file:
                json.dump(default_settings, file, indent=4)
            user_choices["font_manager"] = default_settings["font_manager"]
            user_choices["style_editor"] = default_settings["style_editor"]

        loaded_font = load_fonts()
        if loaded_font:
            dpg.bind_font(loaded_font)
        font_size = user_choices["font_manager"].get("font_size", 20)
        dpg.set_global_font_scale(font_size / 20)

        frame_rounding = user_choices["style_editor"].get("mvStyleVar_FrameRounding", 5)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(
                    dpg.mvStyleVar_FrameRounding,
                    frame_rounding,
                    category=dpg.mvThemeCat_Core,
                )
        dpg.bind_theme(global_theme)
    else:
        default_settings = {
            "font_manager": {"default_font": "Montserrat-SemiBold", "font_size": 20},
            "style_editor": {"mvStyleVar_FrameRounding": 5},
        }
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, "w") as file:
            json.dump(default_settings, file, indent=4)
        load_settings(settings_file)


def Cancel_And_Return(sender, app_data, user_data):
    dpg.delete_item("open_settings")
