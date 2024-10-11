# open_my_gentree.py

import os
import sqlite3
import dearpygui.dearpygui as dpg
from PIL import Image, ImageDraw
import numpy as np
import io

# Specify the directory where the SQLite database will be created
database_dir = os.getcwd()
database_path = os.path.join(database_dir, "family_photos.db")

texture_registry_tag = "global_texture_registry"


class FamilyMember:
    def __init__(self, member_id, name, role, connected_to):
        self.id = member_id
        self.name = name
        self.role = role
        self.connected_to = connected_to
        self.x = 0
        self.y = 0
        self.radius = 40  # Set a default radius
        self.profile_photo = None  # Added to store profile photo


def open_my_gentree(sender, app_data, user_data):
    # Ensure the texture registry exists
    if not dpg.does_item_exist(texture_registry_tag):
        with dpg.texture_registry(tag=texture_registry_tag, show=False):
            pass

    if dpg.does_item_exist("my_gentree_window"):
        dpg.focus_item("my_gentree_window")
    else:
        with dpg.window(
            label="My GenTree",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            on_close=lambda: dpg.delete_item("my_gentree_window"),
            tag="my_gentree_window",
        ):
            conn = sqlite3.connect(database_path)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, role, connected_to FROM people")
                family_members_data = cursor.fetchall()

                # Create member_dict with default radius
                member_dict = {
                    data[0]: FamilyMember(*data) for data in family_members_data
                }

                # Assign specific radii based on roles (if needed)
                for member in member_dict.values():
                    if member.role == "Me":
                        member.radius = 50
                    elif member.role in ["Mom", "Dad"]:
                        member.radius = 40
                    elif member.role in ["Brother", "Sister"]:
                        member.radius = 30
                    else:
                        member.radius = 35  # Default for other roles

                me_member = next(
                    (m for m in member_dict.values() if m.role == "Me"), None
                )

                if me_member:
                    # Load profile photos for all members
                    load_profile_photos(cursor, member_dict)

                    window_width = dpg.get_item_width("my_gentree_window")
                    window_height = dpg.get_item_height("my_gentree_window")
                    center_x = window_width // 2
                    top_y = 100  # Adjust this value to place "Me" closer to the top

                    with dpg.drawlist(
                        parent="my_gentree_window",
                        width=window_width,
                        height=window_height,
                        tag="tree_drawlist",
                    ):
                        me_member.x = center_x
                        me_member.y = top_y
                        draw_family_circle(
                            me_member, "tree_drawlist", color=(255, 0, 0)
                        )

                        # Display siblings
                        display_siblings(
                            cursor, me_member, "tree_drawlist", member_dict
                        )

                        # Recursively display parents and their families
                        display_family_tree(
                            cursor,
                            me_member,
                            "tree_drawlist",
                            member_dict,
                            depth=0,
                            is_root=True,
                        )
            finally:
                conn.close()

            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item("my_gentree_window"),
                parent="my_gentree_window",
            )


def load_profile_photos(cursor, member_dict):
    for member in member_dict.values():
        cursor.execute(
            "SELECT photo FROM photos WHERE person_id = ? AND is_profile_photo = 1",
            (member.id,),
        )
        result = cursor.fetchone()
        if result:
            photo_data = result[0]
            # Convert the binary data to an image
            image = Image.open(io.BytesIO(photo_data))
            image = image.convert("RGBA")
            # Resize the image to fit inside the circle
            image_size = int(member.radius * 2)
            image = image.resize((image_size, image_size), Image.LANCZOS)
            # Create a circular mask
            mask = Image.new("L", (image_size, image_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, image_size, image_size), fill=255)
            # Apply the mask to the image
            image.putalpha(mask)
            member.profile_photo = image


def calculate_dynamic_spacing(depth):
    """
    Calculate dynamic spacing based on the tree depth for separating branches.
    :param depth: The current depth of the tree.
    :return: The calculated spacing for the current level.
    """
    base_branch_spacing = 500
    depth_spacing_factor = (
        -200  # Increase this factor to enlarge spacing at deeper levels
    )
    return base_branch_spacing + (depth * depth_spacing_factor)


def display_family_tree(cursor, member, parent, member_dict, depth, is_root=False):
    # Approximate height of the name text, adjust as needed
    name_height = 25
    # Calculate member_cog_y considering the name height
    member_cog_y = member.y + member.radius + name_height + 10  # Add some padding

    cursor.execute(
        "SELECT id, name, role, connected_to FROM people WHERE connected_to = ? AND role IN ('Mom', 'Dad')",
        (member.id,),
    )
    parents_data = cursor.fetchall()

    # Ensure we don't have more than two parents
    if len(parents_data) > 2:
        parents_data = parents_data[:2]

    # Separate mom and dad
    parents_data = sorted(parents_data, key=lambda x: x[2])

    if not parents_data:
        return

    # Calculate spacing
    branch_spacing = calculate_dynamic_spacing(depth)
    parent_y = member_cog_y + 150  # Adjusted parent Y position
    parent_cog_offset = -60
    parent_cog_y = parent_y + parent_cog_offset

    parent_positions = []
    for i, parent_data in enumerate(parents_data):
        parent_id, parent_name, parent_role, _ = parent_data
        parent_member = member_dict[parent_id]

        # Use dynamic spacing for branches
        if parent_role == "Mom":
            parent_member.x = member.x - branch_spacing // 2
        else:  # Dad
            parent_member.x = member.x + branch_spacing // 2

        parent_member.y = parent_y
        parent_member.radius = 40
        parent_positions.append((parent_member.x, parent_member.y))
        draw_family_circle(parent_member, parent, color=(255, 255, 0))

        # Draw line from parent to parent_cog_y
        dpg.draw_line(
            (int(parent_member.x), int(parent_member.y - parent_member.radius)),
            (int(parent_member.x), int(parent_cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

        display_family_tree(cursor, parent_member, parent, member_dict, depth + 1)
        display_siblings(cursor, parent_member, parent, member_dict)

    if len(parents_data) > 1:
        parent_positions.sort()
        parent_mid_x = sum(x for x, _ in parent_positions) // len(parent_positions)
        dpg.draw_line(
            (int(parent_positions[0][0]), int(parent_cog_y)),
            (int(parent_positions[-1][0]), int(parent_cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )
    else:
        parent_mid_x = parent_positions[0][0]

    # Draw line from member to member_cog_y
    dpg.draw_line(
        (int(member.x), int(member.y + member.radius + name_height)),
        (int(member.x), int(member_cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )

    # Draw vertical line connecting member and parents
    dpg.draw_line(
        (int(member.x), int(member_cog_y)),
        (int(parent_mid_x), int(member_cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )

    dpg.draw_line(
        (int(parent_mid_x), int(member_cog_y)),
        (int(parent_mid_x), int(parent_cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )


def display_siblings(cursor, member, parent, member_dict):
    cursor.execute(
        "SELECT id, name, role, connected_to FROM people WHERE connected_to = ? AND role IN ('Brother', 'Sister')",
        (member.id,),
    )
    siblings_data = cursor.fetchall()
    siblings_data.sort(key=lambda x: x[0])

    if not siblings_data:
        return False

    sibling_spacing = 100
    cog_offset = 60
    sibling_y = member.y
    cog_y = sibling_y + cog_offset

    sister_x = member.x - sibling_spacing
    brother_x = member.x + sibling_spacing

    sibling_positions = []
    for sibling_data in siblings_data:
        sibling_id, sibling_name, sibling_role, _ = sibling_data
        sibling_member = member_dict[sibling_id]
        if sibling_role == "Sister":
            sibling_member.x = sister_x
            sister_x -= sibling_spacing
        else:  # Brother
            sibling_member.x = brother_x
            brother_x += sibling_spacing

        sibling_member.y = sibling_y
        sibling_member.radius = 30
        sibling_positions.append((sibling_member.x, sibling_member.y))
        draw_family_circle(sibling_member, parent, color=(0, 255, 0))

        # Draw vertical line from sibling to cog_y
        dpg.draw_line(
            (int(sibling_member.x), int(sibling_member.y + sibling_member.radius)),
            (int(sibling_member.x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    if sibling_positions:
        sibling_positions.sort()
        leftmost_x = sibling_positions[0][0]
        rightmost_x = sibling_positions[-1][0]

        # Draw horizontal line connecting siblings at cog_y
        dpg.draw_line(
            (int(leftmost_x), int(cog_y)),
            (int(rightmost_x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    # Draw line from "Me" to cog_y
    member_cog_y = member.y + member.radius + 10  # Adjust as needed
    dpg.draw_line(
        (int(member.x), int(member.y + member.radius)),
        (int(member.x), int(member_cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )
    dpg.draw_line(
        (int(member.x), int(member_cog_y)),
        (int(member.x), int(cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )

    # Draw horizontal line connecting "Me" to siblings at cog_y
    if sibling_positions:
        x_positions = [pos[0] for pos in sibling_positions] + [member.x]
        leftmost_x = min(x_positions)
        rightmost_x = max(x_positions)
        dpg.draw_line(
            (int(leftmost_x), int(cog_y)),
            (int(rightmost_x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    return True


def draw_family_circle(member, parent, color):
    # Draw the circle
    dpg.draw_circle(
        center=(int(member.x), int(member.y)),
        radius=int(member.radius),
        color=color,
        fill=(*color[:3], 100),
        parent=parent,
    )
    # Draw the profile photo if available
    if member.profile_photo:
        # Create a texture from the profile photo
        texture_tag = f"profile_texture_{member.id}"
        if not dpg.does_item_exist(texture_tag):
            image = member.profile_photo
            width, height = image.size
            pixel_data = np.array(image).flatten() / 255.0
            dpg.add_static_texture(
                width, height, pixel_data, tag=texture_tag, parent=texture_registry_tag
            )
        # Draw the image inside the circle
        dpg.draw_image(
            texture_tag,
            pmin=(int(member.x - member.radius), int(member.y - member.radius)),
            pmax=(int(member.x + member.radius), int(member.y + member.radius)),
            parent=parent,
        )

    # Draw the name below the circle
    text_width = dpg.get_text_size(member.name)[0]
    text_height = dpg.get_text_size(member.name)[1]
    text_x = int(member.x - text_width / 2)
    text_y = int(member.y + member.radius + 5)  # Position the name below the circle
    dpg.draw_text(
        pos=(text_x, text_y),
        text=member.name,
        size=18,
        color=(255, 255, 255, 255),
        parent=parent,
    )
