import dearpygui.dearpygui as dpg
import os

# Get the directory of the main script
main_directory = os.path.dirname(os.path.abspath(__name__))

# Append the specific path to the cairo DLLs relative to the main_directory
cairo_dll_path = os.path.join(main_directory, "env", "Lib", "site-packages", "cairo-windows-1.15.12", "lib", "x64")

# Set the correct path to include Cairo DLLs in the environment variable
os.environ["PATH"] += ";" + cairo_dll_path

# Now you can import cairosvg or other libraries that depend on these DLLs
import cairosvg

def setup_logo(scale_factor=0.9):
    svg_file_path = "Data/Figures/GenTree_Logo.svg"
    png_file_path = "Data/Figures/GenTree_Logo.png"

    if os.path.exists(svg_file_path):
        # Convert SVG to PNG with scaling
        cairosvg.svg2png(
            url=svg_file_path,
            write_to=png_file_path,
            scale=scale_factor  # Apply the scaling factor
        )

    if os.path.exists(png_file_path):
        width, height, channels, data = dpg.load_image(png_file_path)
        with dpg.texture_registry(show=False):
            texture_id = dpg.add_static_texture(
                width=width, height=height, default_value=data
            )
        return texture_id, width, height

    return None, 0, 0  # In case of errors

