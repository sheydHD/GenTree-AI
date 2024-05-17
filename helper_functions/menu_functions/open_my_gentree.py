import os
import sqlite3
import dearpygui.dearpygui as dpg

# database_path = os.path.join("C:\\sqlite", "family_photos.db")

# Specify the directory where the SQLite database will be created
database_dir = os.getcwd()
database_path = os.path.join(database_dir, "family_photos.db")


class FamilyMember:
    def __init__(self, member_id, name, role, connected_to):
        self.id = member_id
        self.name = name
        self.role = role
        self.connected_to = connected_to
        self.x = 0
        self.y = 0
        self.radius = 0


def open_my_gentree(sender, app_data, user_data):
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

                member_dict = {
                    data[0]: FamilyMember(*data) for data in family_members_data
                }
                me_member = next(
                    (m for m in member_dict.values() if m.role == "Me"), None
                )

                if me_member:
                    window_width = dpg.get_item_width("my_gentree_window")
                    window_height = dpg.get_item_height("my_gentree_window")
                    center_x = window_width // 2
                    center_y = window_height // 2

                    with dpg.drawlist(
                        parent="my_gentree_window",
                        width=window_width,
                        height=window_height,
                        tag="tree_drawlist",
                    ):
                        me_member.x = center_x
                        me_member.y = center_y
                        me_member.radius = 50
                        draw_family_circle(
                            me_member, "tree_drawlist", color=(255, 0, 0)
                        )

                        # Recursively display parents and siblings
                        display_family_tree(
                            cursor, me_member, "tree_drawlist", depth=0, is_root=True
                        )
            finally:
                conn.close()

            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item("my_gentree_window"),
                parent="my_gentree_window",
            )


def calculate_spacing(cursor, member):
    mom_count = count_family_members(cursor, member, "Mom")
    dad_count = count_family_members(cursor, member, "Dad")
    additional_spacing = max(mom_count, dad_count) * 50
    base_spacing = 200
    return base_spacing + additional_spacing


def display_family_tree(cursor, member, parent, depth, is_root=False):
    sibling_present = display_siblings(
        cursor,
        member,
        parent,
        direction="left" if member.role == "Mom" else "right",
        depth=depth,
    )

    member_cog_y = member.y + 60

    cursor.execute(
        "SELECT id, name, role, connected_to FROM people WHERE connected_to = ? AND role IN ('Mom', 'Dad')",
        (member.id,),
    )
    parents_data = cursor.fetchall()

    if not parents_data:
        return

    # Calculate consistent spacing
    parent_spacing = calculate_spacing(cursor, member)
    parent_y = member.y + 150
    parent_cog_offset = -60
    parent_cog_y = parent_y + parent_cog_offset

    parent_positions = []
    for i, parent_data in enumerate(parents_data):
        parent_id, parent_name, parent_role, _ = parent_data
        parent_member = FamilyMember(parent_id, parent_name, parent_role, member.id)
        parent_member.x = member.x - parent_spacing // 2 + (i * parent_spacing)
        parent_member.y = parent_y
        parent_member.radius = 40
        parent_positions.append((parent_member.x, parent_member.y))
        draw_family_circle(parent_member, parent, color=(255, 255, 0))

        dpg.draw_line(
            (int(parent_member.x), int(parent_member.y - parent_member.radius)),
            (int(parent_member.x), int(parent_cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

        # Display siblings on the correct side
        sibling_present = display_siblings(
            cursor,
            parent_member,
            parent,
            direction="left" if parent_role == "Mom" else "right",
            depth=depth + 1,
        )

        display_family_tree(cursor, parent_member, parent, depth + 1)

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

    if sibling_present or parents_data:
        dpg.draw_line(
            (int(member.x), int(member.y + member.radius)),
            (int(member.x), int(member_cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

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


def display_siblings(cursor, member, parent, direction="left", depth=0):
    cursor.execute(
        "SELECT id, name, role, connected_to FROM people WHERE role IN ('Brother', 'Sister') AND connected_to = ?",
        (member.id,),
    )
    siblings_data = cursor.fetchall()
    siblings_data.sort(key=lambda x: x[0])

    if not siblings_data:
        return False

    sibling_spacing = 100 + depth * 50
    cog_offset = 60
    sibling_y = member.y
    cog_y = sibling_y + cog_offset

    if direction == "left":
        sibling_x = member.x - 120 - depth * 50
    else:
        sibling_x = member.x + 120 + depth * 50

    for i, sibling_data in enumerate(siblings_data):
        sibling_id, sibling_name, sibling_role, _ = sibling_data
        sibling_member = FamilyMember(sibling_id, sibling_name, sibling_role, member.id)
        sibling_member.x = (
            sibling_x - i * sibling_spacing
            if direction == "left"
            else sibling_x + i * sibling_spacing
        )
        sibling_member.y = sibling_y
        sibling_member.radius = 30
        draw_family_circle(sibling_member, parent, color=(0, 255, 0))

        dpg.draw_line(
            (int(sibling_member.x), int(sibling_member.y + sibling_member.radius)),
            (int(sibling_member.x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    if siblings_data:
        if direction == "left":
            start_x = sibling_x - (len(siblings_data) - 1) * sibling_spacing
            end_x = sibling_x
        else:
            start_x = sibling_x
            end_x = sibling_x + (len(siblings_data) - 1) * sibling_spacing

        dpg.draw_line(
            (int(start_x), int(cog_y)),
            (int(end_x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    member_cog_y = member.y + cog_offset
    dpg.draw_line(
        (int(member.x), int(member.y + member.radius)),
        (int(member.x), int(member_cog_y)),
        color=(255, 255, 255, 255),
        thickness=2,
        parent=parent,
    )

    if siblings_data:
        dpg.draw_line(
            (int(member.x), int(member_cog_y)),
            (int(sibling_x), int(cog_y)),
            color=(255, 255, 255, 255),
            thickness=2,
            parent=parent,
        )

    return True


def count_family_members(cursor, member, role):
    cursor.execute(
        "SELECT COUNT(*) FROM people WHERE connected_to = ? AND role = ?",
        (member.id, role),
    )
    count = cursor.fetchone()[0]
    return count


def draw_family_circle(member, parent, color):
    dpg.draw_circle(
        center=(int(member.x), int(member.y)),
        radius=int(member.radius),
        color=color,
        fill=(*color[:3], 100),
        parent=parent,
    )
    dpg.draw_text(
        pos=(int(member.x) - 50, int(member.y) - 10),
        text=member.name,
        size=18,
        color=(255, 255, 255, 255),
        parent=parent,
    )
