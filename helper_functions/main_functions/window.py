# window.py

import dearpygui.dearpygui as dpg
from helper_functions.main_functions.logo import setup_logo
from helper_functions.main_functions.menu import setup_buttons


def setup_window(font):
    with dpg.window(
        tag="Primary Window",
        no_resize=True,
        no_move=True,
        no_scrollbar=True,
        no_collapse=True,
        no_close=True,
        no_background=True,
        autosize=True,
    ):
        texture_id, width, height = setup_logo()
        setup_buttons(texture_id, width, height, font)
