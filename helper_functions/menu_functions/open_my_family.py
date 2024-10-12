# open_my_family.py

import dearpygui.dearpygui as dpg
import sqlite3
import os
import time
from PIL import Image
import io
import numpy as np
import face_recognition
from helper_functions.menu_functions.open_my_gentree import open_my_gentree

# database_path = os.path.join("C:\\sqlite", "family_photos.db")

# Specify the directory where the SQLite database will be created
database_dir = os.getcwd()
database_path = os.path.join(database_dir, "family_photos.db")


def open_my_family(sender, app_data, user_data):
    if dpg.does_item_exist("my_family_window"):
        dpg.focus_item("my_family_window")
    else:
        with dpg.window(
            label="My Family",
            width=1920,
            height=1080,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag="my_family_window",
            on_close=lambda: dpg.delete_item("my_family_window"),
        ):
            # Create a new SQLite connection and cursor within this function
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            # Retrieve family members from the SQLite database
            cursor.execute("SELECT id, name, role, connected_to FROM people")
            family_members = cursor.fetchall()

            # Create a group to hold the family member entries
            with dpg.group(tag="member_group"):
                if family_members:
                    for (
                        member_id,
                        member_name,
                        member_role,
                        connected_to,
                    ) in family_members:
                        # Get the connected_to person's name
                        if connected_to:
                            cursor.execute(
                                "SELECT name FROM people WHERE id = ?", (connected_to,)
                            )
                            connected_to_name_result = cursor.fetchone()
                            if connected_to_name_result:
                                connected_to_name = connected_to_name_result[0]
                            else:
                                connected_to_name = "Unknown"
                        else:
                            connected_to_name = None

                        if member_role == "Me":
                            label = f"{member_name} ({member_role})"
                        else:
                            if connected_to_name:
                                label = f"{member_name} ({connected_to_name})({member_role})"
                            else:
                                label = f"{member_name} (No Connection)({member_role})"

                        # Create a group for each member to hold their information and buttons
                        with dpg.group(horizontal=True):
                            # Button to open member photos
                            dpg.add_button(
                                label=label,
                                callback=lambda s, a, u: open_member_photos(u),
                                user_data=member_id,
                                tag=f"member_button_{member_id}",
                                width=400,  # Adjust width as needed
                            )
                            # Modify button
                            dpg.add_button(
                                label="Modify",
                                callback=modify_family_member,
                                user_data=(member_id, member_name),
                                tag=f"modify_button_{member_id}",
                            )
                            # Remove button
                            dpg.add_button(
                                label="Remove",
                                callback=remove_family_member,
                                user_data=(member_id, member_name),
                                tag=f"remove_button_{member_id}",
                            )
                else:
                    dpg.add_text("No family members found.")

            # Add a button to close the window
            dpg.add_button(
                label="Close", callback=lambda: dpg.delete_item("my_family_window")
            )

            # Close the SQLite connection
            conn.close()


def open_member_photos(member_id):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Retrieve the member's name from the SQLite database
    cursor.execute("SELECT name FROM people WHERE id = ?", (member_id,))
    member_name = cursor.fetchone()[0]

    # Open a new window to display the photos of the selected family member
    window_tag = f"member_window_{member_id}"
    if dpg.does_item_exist(window_tag):
        # If the member window is already open, bring it to the front
        dpg.focus_item(window_tag)
    else:
        # If the member window is closed, create a new one
        window_width = 1920
        window_height = 1080
        with dpg.window(
            label=f"{member_name}'s Photos",
            width=window_width,
            height=window_height,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            tag=window_tag,
        ):
            # Retrieve photos for the selected family member from the SQLite database
            cursor.execute(
                "SELECT id, photo FROM photos WHERE person_id = ?", (member_id,)
            )
            photos = cursor.fetchall()

            texture_tags = []
            max_size = (250, 250)  # Ensure max_size is defined

            if photos:
                # Create a unique texture registry for this member
                with dpg.texture_registry(
                    tag=f"texture_registry_{member_id}", show=False
                ):
                    for photo_id, photo_data in photos:
                        try:
                            # Convert the binary data to an image
                            image = Image.open(io.BytesIO(photo_data))
                            image = image.convert(
                                "RGBA"
                            )  # Ensure image is in RGBA format

                            # Resize the image to a maximum of 250x250 pixels, preserving aspect ratio
                            image.thumbnail(max_size, Image.LANCZOS)

                            width, height = image.size
                            # Get pixel data and normalize it
                            pixel_data = np.array(image).flatten() / 255.0

                            # Create a texture
                            texture_tag = f"texture_{photo_id}"
                            dpg.add_static_texture(
                                width,
                                height,
                                pixel_data,
                                tag=texture_tag,
                                parent=f"texture_registry_{member_id}",
                            )
                            texture_tags.append((photo_id, texture_tag, width, height))
                        except Exception as e:
                            print(f"Error processing image ID {photo_id}: {e}")

                # Calculate number of columns based on window width and image width
                padding = 10  # Adjust as needed
                image_width = max_size[0]
                columns = max(1, window_width // (image_width + padding))

                # Now, display the images in a table
                with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit):
                    for _ in range(columns):
                        dpg.add_table_column()

                    for index in range(0, len(texture_tags), columns):
                        with dpg.table_row():
                            for photo_id, texture_tag, width, height in texture_tags[
                                index : index + columns
                            ]:
                                with dpg.table_cell():
                                    dpg.add_image(
                                        texture_tag, width=width, height=height
                                    )
                                    dpg.add_button(
                                        label="Remove",
                                        user_data=(member_id, photo_id),
                                        callback=lambda s, a, u: remove_photo(
                                            u[0], u[1]
                                        ),
                                    )
            else:
                # If no photos, display a message
                dpg.add_text("No photos available.")

            # Add a button to close the window
            dpg.add_button(
                label="Close",
                callback=lambda: close_member_window(member_id),
            )

    # Close the SQLite connection
    conn.close()


def remove_family_member(sender, app_data, user_data):
    member_id, member_name = user_data
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
        try:
            connected_to = int(new_connection.split("(ID: ")[1].split(")")[0])
        except (IndexError, ValueError):
            connected_to = None
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

    # Remove the success message after 1 second
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message)


def close_member_window(member_id):
    # Delete the member window
    dpg.delete_item(f"member_window_{member_id}")
    # Delete the associated texture registry
    if dpg.does_item_exist(f"texture_registry_{member_id}"):
        dpg.delete_item(f"texture_registry_{member_id}")


def remove_photo(member_id, photo_id):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Check if the photo to be deleted is the profile photo
    cursor.execute("SELECT is_profile_photo FROM photos WHERE id = ?", (photo_id,))
    result = cursor.fetchone()
    if result:
        is_profile_photo = result[0]
    else:
        is_profile_photo = 0  # Photo doesn't exist

    # Remove the selected photo from the photos table
    cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()

    if is_profile_photo == 1:
        # Check if there are other photos for the member
        cursor.execute(
            "SELECT id, photo FROM photos WHERE person_id = ? LIMIT 1", (member_id,)
        )
        new_photo = cursor.fetchone()
        if new_photo:
            new_photo_id, photo_data = new_photo
            # Process the photo to extract the face
            face_photo_data = process_photo_data_to_extract_face(photo_data)
            if face_photo_data:
                # Update the photo record to set is_profile_photo = 1
                cursor.execute(
                    "UPDATE photos SET is_profile_photo = 1 WHERE id = ?",
                    (new_photo_id,),
                )
                # Update the photo data with the processed face image
                cursor.execute(
                    "UPDATE photos SET photo = ? WHERE id = ?",
                    (face_photo_data, new_photo_id),
                )
            else:
                # If face extraction failed, set is_profile_photo = 0
                cursor.execute(
                    "UPDATE photos SET is_profile_photo = 0 WHERE id = ?",
                    (new_photo_id,),
                )
        else:
            # No other photos, nothing to do
            pass
        conn.commit()

    # Close the SQLite connection
    conn.close()

    # Remove the message and spinner after processing
    dpg.delete_item("processing_group")

    # Delete the texture associated with the photo
    if dpg.does_item_exist(f"texture_{photo_id}"):
        dpg.delete_item(f"texture_{photo_id}")

    # Refresh the member window
    dpg.delete_item(f"member_window_{member_id}")
    close_member_window(member_id)
    open_member_photos(member_id)

    # Update the GenTree if it's open
    if dpg.does_item_exist("my_gentree_window"):
        # Close and reopen the GenTree window to refresh it
        dpg.delete_item("my_gentree_window")
        open_my_gentree(None, None, None)


def process_photo_data_to_extract_face(photo_data):
    # Load the image from bytes
    image = face_recognition.load_image_file(io.BytesIO(photo_data))
    # Find face locations
    face_locations = face_recognition.face_locations(image)
    if face_locations:
        # Take the first face location
        top, right, bottom, left = face_locations[0]
        # Add margin
        margin = 30  # Same as before
        # Ensure the new coordinates are within image bounds
        top = max(0, top - margin)
        right = min(image.shape[1], right + margin)
        bottom = min(image.shape[0], bottom + margin)
        left = max(0, left - margin)
        # Crop the image to the face with margin
        face_image = image[top:bottom, left:right]
        # Convert the image to bytes
        pil_image = Image.fromarray(face_image)
        # Resize the image to a standard size, e.g., 100x100
        pil_image = pil_image.resize((100, 100), Image.LANCZOS)
        # Save the image to bytes
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format="PNG")
        face_photo_data = img_byte_arr.getvalue()
        return face_photo_data
    else:
        return None
