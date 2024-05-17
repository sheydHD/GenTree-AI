import dearpygui.dearpygui as dpg
import sqlite3
import os
import time

# database_path = os.path.join("C:\\sqlite", "family_photos.db")

# Specify the directory where the SQLite database will be created
database_dir = os.getcwd()
database_path = os.path.join(database_dir, "family_photos.db")


def open_my_family(sender, app_data, user_data):
    # Check if the "My Family" window is already open
    if dpg.does_item_exist("my_family_window"):
        # If the window is open, bring it to the front
        dpg.focus_item("my_family_window")
    else:
        # If the window is closed, create a new one
        with dpg.window(
            label="My Family",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag="my_family_window",
        ):
            # Add a text label to the new window
            dpg.add_text("Family Members:")

            # Create a new SQLite connection and cursor within this function
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            # Retrieve family members from the SQLite database
            cursor.execute("SELECT id, name, role FROM people")
            family_members = cursor.fetchall()

            # Close the SQLite connection
            conn.close()

            # Create a group to hold the family member buttons
            with dpg.group(tag="member_group"):
                for member_id, member_name, member_role in family_members:
                    display_name = f"{member_name} ({member_role})"
                    with dpg.group(horizontal=True, tag=f"member_group_{member_id}"):
                        dpg.add_button(
                            label=display_name,
                            user_data=(member_id),
                            tag=f"member_button_{member_id}",
                            callback=lambda s, a, u: open_member_photos(u),
                        )
                        dpg.add_button(
                            label="Remove",
                            user_data=(member_id, member_name),
                            callback=remove_family_member,
                        )
                        dpg.add_button(
                            label="Modify",
                            user_data=(member_id, member_name),
                            callback=modify_family_member,
                        )

            # Add a button to close the window
            dpg.add_button(
                label="Close", callback=lambda: dpg.delete_item("my_family_window")
            )


def open_member_photos(member_id):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Retrieve the member's name from the SQLite database
    cursor.execute("SELECT name FROM people WHERE id = ?", (member_id,))
    member_name = cursor.fetchone()[0]

    # Open a new window to display the photos of the selected family member
    if dpg.does_item_exist(f"member_window_{member_id}"):
        # If the member window is already open, bring it to the front
        dpg.focus_item(f"member_window_{member_id}")
    else:
        # If the member window is closed, create a new one
        with dpg.window(
            label=f"{member_name}'s Photos",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag=f"member_window_{member_id}",
        ):
            # Retrieve photos for the selected family member from the SQLite database
            cursor.execute(
                "SELECT id, photo FROM photos WHERE person_id = ?", (member_id,)
            )
            photos = cursor.fetchall()

            for photo_id, photo_data in photos:
                with dpg.group(horizontal=True):
                    dpg.add_text(f"Photo ID: {photo_id}")
                    dpg.add_button(
                        label="Remove",
                        user_data=(member_id, photo_id),
                        callback=lambda s, a, u: remove_photo(u[0], u[1]),
                    )

            # Add a button to close the window
            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item(f"member_window_{member_id}"),
            )

    # Close the SQLite connection
    conn.close()


def remove_family_member(sender, app_data, user_data):
    # Remove the selected family member from the SQLite database
    member_id = user_data[0]
    member_name = user_data[1]

    # Create a custom confirmation dialog
    with dpg.window(
        label="Confirm Deletion",
        modal=True,
        no_title_bar=True,
        pos=(300, 300),
        tag=f"confirm_dialog_{member_id}",
    ):
        dpg.add_text(f"Are you sure you want to remove member {member_name}?")
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Yes",
                callback=lambda: remove_member_from_database(member_id, member_name),
            )
            dpg.add_button(
                label="No",
                callback=lambda: dpg.delete_item(f"confirm_dialog_{member_id}"),
            )


def remove_member_from_database(member_id, member_name):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Remove the family member from the people table
    cursor.execute("DELETE FROM people WHERE id = ?", (member_id,))

    # Remove the associated photos from the photos table
    cursor.execute("DELETE FROM photos WHERE person_id = ?", (member_id,))

    conn.commit()

    # Close the SQLite connection
    conn.close()

    dpg.delete_item(f"member_group_{member_id}")
    success_message2 = dpg.add_text(
        f"Member {member_name} has been removed.", parent="my_family_window"
    )
    dpg.delete_item(f"confirm_dialog_{member_id}")

    # Remove the success message after 3 seconds
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message2)


def modify_family_member(sender, app_data, user_data):
    member_id, member_name = user_data

    # Create a custom modification dialog
    with dpg.window(
        label="Modify Member",
        width=1920,
        height=1080,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        modal=True,
        no_title_bar=True,
        # pos=(300, 300),
        tag=f"modify_dialog_{member_id}",
    ):
        dpg.add_text(f"Modify details for member {member_name}:")
        dpg.add_input_text(tag=f"new_name_{member_id}", label="Name")

        dpg.add_radio_button(
            tag=f"new_role_{member_id}",
            items=[
                "Me",
                "Mom",
                "Dad",
                "Sister",
                "Brother",
            ],
        )

        with dpg.group(tag=f"connection_group_{member_id}"):
            dpg.add_text("Select the person to whom this person is connected:")
            # Create a new SQLite connection and cursor within this function
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM people WHERE id != ?", (member_id,))
            people = cursor.fetchall()

            # Close the SQLite connection
            conn.close()

            if people:
                people_names = [
                    f"{i+1}. {person_name}"
                    for i, (person_id, person_name) in enumerate(people)
                ]
                dpg.add_radio_button(
                    tag=f"new_connection_{member_id}",
                    items=people_names,
                    default_value=None,
                )
            else:
                dpg.add_text("No family members found.")

        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Save",
                callback=lambda: update_member_details(member_id),
            )
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item(f"modify_dialog_{member_id}"),
            )


def modify_family_member(sender, app_data, user_data):
    member_id, member_name = user_data

    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Retrieve the current details of the family member from the database
    cursor.execute(
        "SELECT name, role, connected_to FROM people WHERE id = ?", (member_id,)
    )
    current_details = cursor.fetchone()
    current_name, current_role, current_connected_to = current_details

    # Close the SQLite connection
    conn.close()

    # Create a custom modification dialog
    with dpg.window(
        label="Modify Member",
        width=1920,
        height=1080,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        no_close=True,
        modal=True,
        no_title_bar=True,
        tag=f"modify_dialog_{member_id}",
    ):
        dpg.add_text(f"Modify details for member {member_name}:")
        dpg.add_input_text(
            tag=f"new_name_{member_id}", label="Name", default_value=current_name
        )

        dpg.add_text("Who is the person in the family:")
        dpg.add_radio_button(
            tag=f"new_role_{member_id}",
            items=[
                "None",
                "Me",
                "Mom",
                "Dad",
                "Sister",
                "Brother",
            ],
            default_value=current_role,
        )

        with dpg.group(tag=f"connection_group_{member_id}"):
            dpg.add_text("Select the person to whom this person is connected:")
            # Create a new SQLite connection and cursor within this function
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM people WHERE id != ?", (member_id,))
            people = cursor.fetchall()

            # Close the SQLite connection
            conn.close()

            if people:
                people_options = ["None"] + [
                    f"{person_name} (ID: {person_id})"
                    for person_id, person_name in people
                ]
                dpg.add_radio_button(
                    tag=f"new_connection_{member_id}",
                    items=people_options,
                    default_value=f"{next((name for pid, name in people if pid == current_connected_to), '')} (ID: {current_connected_to})",
                )
            else:
                dpg.add_text("No other family members found.")

        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Save",
                callback=lambda: update_member_details(member_id),
            )
            dpg.add_button(
                label="Cancel",
                callback=lambda: dpg.delete_item(f"modify_dialog_{member_id}"),
            )


def update_member_details(member_id):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Retrieve the current details of the family member from the database
    cursor.execute(
        "SELECT name, role, connected_to FROM people WHERE id = ?", (member_id,)
    )
    current_details = cursor.fetchone()
    current_name, current_role, current_connected_to = current_details

    # Update the family member's details in the people table
    new_name = dpg.get_value(f"new_name_{member_id}") or current_name
    new_role = dpg.get_value(f"new_role_{member_id}") or current_role
    new_connection = dpg.get_value(f"new_connection_{member_id}")

    if new_connection and new_connection != "None":
        connected_to = int(new_connection.split("(ID: ")[1].split(")")[0])
    else:
        connected_to = None

    cursor.execute(
        "UPDATE people SET name = ?, role = ?, connected_to = ? WHERE id = ?",
        (new_name, new_role, connected_to, member_id),
    )
    conn.commit()

    # Close the SQLite connection
    conn.close()

    # Update the button label in the "My Family" window
    dpg.set_item_label(f"member_button_{member_id}", f"{new_name} ({new_role})")

    # Close the modification dialog
    dpg.delete_item(f"modify_dialog_{member_id}")

    # Show a success message
    success_message = dpg.add_text(
        f"Member {member_id}'s details have been updated.",
        parent="my_family_window",
    )

    # Remove the success message after 1 seconds
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message)


def remove_photo(member_id, photo_id):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Remove the selected photo from the photos table
    cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()

    # Close the SQLite connection
    conn.close()

    # Refresh the member window
    dpg.delete_item(f"member_window_{member_id}")
    open_member_photos(member_id)
