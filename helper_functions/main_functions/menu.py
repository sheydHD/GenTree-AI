# menu,py

import dearpygui.dearpygui as dpg
from helper_functions.menu_functions.open_my_family import open_my_family
from helper_functions.menu_functions.open_my_gentree import open_my_gentree
from helper_functions.menu_functions.open_settings import open_settings
from helper_functions.menu_functions.add_new_photo import add_new_photo


def quit_app(sender, app_data, user_data):
    dpg.stop_dearpygui()


def setup_buttons(texture_id, logo_width, logo_height, font):
    if texture_id is None:
        return  # Exit if texture loading failed

    window_width = dpg.get_viewport_width()
    logo_pos = (window_width - logo_width) // 2, 20
    dpg.add_image(texture_id, parent="Primary Window", pos=logo_pos)

    # Bind the font
    dpg.bind_font(font)

    button_width = 200
    button_height = 50
    button_spacing = 10
    start_y = logo_pos[1] + logo_height + 50

    button_props = {
        "width": button_width,
        "height": button_height,
        "parent": "Primary Window",
    }

    buttons = [
        ("Open My GenTree", open_my_gentree),
        ("Add new photo", add_new_photo),
        ("My Family", open_my_family),
        ("Settings", open_settings),
        ("Quit", quit_app),
    ]

    for i, (label, callback) in enumerate(buttons):
        dpg.add_button(
            label=label,
            callback=callback,
            pos=(
                (window_width - button_width) // 2,
                start_y + i * (button_height + button_spacing),
            ),
            **button_props
        )
