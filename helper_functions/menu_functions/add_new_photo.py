# add_new_photo.py
import dearpygui.dearpygui as dpg
import os
import sqlite3
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import cv2
import face_recognition
import numpy as np
from PIL import Image
import io

# Specify the directory where the SQLite database will be created
database_dir = os.getcwd()
database_path = os.path.join(database_dir, "family_photos.db")
conn = sqlite3.connect(database_path)


# Modify the database schema to add 'is_profile_photo' column
def modify_database_schema():
    cursor = conn.cursor()
    try:
        cursor.execute(
            "ALTER TABLE photos ADD COLUMN is_profile_photo INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        # Column already exists
        pass
    conn.commit()


modify_database_schema()


def add_new_photo(sender, app_data, user_data):
    # Open a file dialog to select a photo
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    file_path = askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])

    if file_path:
        # Show the "Analyzing photo" popup
        with dpg.window(
            label="Analyzing Photo",
            width=200,
            height=50,
            pos=(
                (dpg.get_viewport_width() - 200) // 2 - 10,
                (dpg.get_viewport_height() - 50) // 2,
            ),
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_title_bar=True,
            tag="analyzing_photo_window",
        ):
            dpg.add_text("Analyzing photo...")
            dpg.add_loading_indicator(
                style=1,
                pos=(
                    200 // 2 - 20,
                    50 // 2 + 10,
                ),
            )

        recognized_person = recognize_person(file_path)

        # Close the confirmation window
        dpg.delete_item("analyzing_photo_window")

        if recognized_person:
            # Display the recognized person's name and ask for confirmation
            with dpg.window(
                label="Confirm Person",
                width=1920,
                height=1020,
                no_move=True,
                no_resize=True,
                no_collapse=True,
                tag="confirm_person_window",
            ):

                dpg.add_text(f"Is this person {recognized_person}?")
                dpg.add_button(
                    label="Yes",
                    callback=lambda: confirm_person(file_path, recognized_person),
                )
                dpg.add_button(label="No", callback=lambda: handle_no_answer(file_path))
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.delete_item("confirm_person_window"),
                )
        else:
            handle_no_answer(file_path)


def handle_no_answer(file_path):
    # Close the "Confirm Person" window if it exists
    if dpg.does_item_exist("confirm_person_window"):
        dpg.delete_item("confirm_person_window")

    # Create a new window to select an existing person or add a new person
    with dpg.window(
        label="Select Person",
        width=1920,
        height=1080,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        tag="select_person_window",
    ):
        dpg.add_text(
            "Person not recognized, select an existing person or add a new person:"
        )
        dpg.add_button(
            label="Select family member",
            callback=lambda: handle_already_in_family(file_path),
        )
        dpg.add_button(
            label="Add New Person", callback=lambda: handle_new_person(file_path)
        )
        dpg.add_button(
            label="Cancel",
            callback=lambda: dpg.delete_item("select_person_window"),
        )


def recognize_person(file_path):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Load known face encodings from the database
    cursor.execute(
        "SELECT people.name, photos.photo FROM photos JOIN people ON photos.person_id = people.id"
    )
    known_faces = {}
    for row in cursor.fetchall():
        name = row[0]
        photo_data = row[1]

        # Convert the photo data to a numpy array
        nparr = np.frombuffer(photo_data, np.uint8)
        photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Generate face encoding for the photo
        face_encodings = face_recognition.face_encodings(photo)
        if face_encodings:
            face_encoding = face_encodings[0]
            if name not in known_faces:
                known_faces[name] = []
            known_faces[name].append(face_encoding)

    # Close the SQLite connection
    conn.close()

    # Read the input photo
    input_photo = face_recognition.load_image_file(file_path)

    # Find all face locations in the input photo
    face_locations = face_recognition.face_locations(input_photo)
    face_encodings = face_recognition.face_encodings(input_photo, face_locations)

    recognized_person = None
    for face_encoding in face_encodings:
        # Compare the current face encoding with known faces
        for name, encodings in known_faces.items():
            matches = face_recognition.compare_faces(encodings, face_encoding)
            if True in matches:
                recognized_person = name
                break

    return recognized_person


def confirm_person(file_path, person_name):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Add the photo to the confirmed person
    cursor.execute("SELECT id FROM people WHERE name = ?", (person_name,))
    person_id = cursor.fetchone()[0]

    with open(file_path, "rb") as file:
        photo_data = file.read()

    # Insert the original photo
    cursor.execute(
        "INSERT INTO photos (person_id, photo) VALUES (?, ?)", (person_id, photo_data)
    )

    # Check if the person already has a profile photo
    cursor.execute(
        "SELECT COUNT(*) FROM photos WHERE person_id = ? AND is_profile_photo = 1",
        (person_id,),
    )
    has_profile_photo = cursor.fetchone()[0] > 0

    if not has_profile_photo:
        # Process the photo to extract the face
        face_photo_data = process_photo_to_extract_face(file_path)
        if face_photo_data:
            # Insert the face photo as the profile photo
            cursor.execute(
                "INSERT INTO photos (person_id, photo, is_profile_photo) VALUES (?, ?, 1)",
                (person_id, face_photo_data),
            )
        else:
            # Inform the user that no face was detected
            dpg.add_text("No face detected in the photo.", parent="Primary Window")

    conn.commit()
    conn.close()

    # Close the confirmation window
    dpg.delete_item("confirm_person_window")

    # Show a success message
    success_message = dpg.add_text(
        f"Photo added to {person_name}.", parent="Primary Window"
    )

    # Remove the success message after 1 second
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message)


def process_photo_to_extract_face(file_path):
    # Load the image
    image = face_recognition.load_image_file(file_path)
    # Find face locations
    face_locations = face_recognition.face_locations(image)
    if face_locations:
        # Take the first face location
        top, right, bottom, left = face_locations[0]
        # Add margin
        margin = 30  # Increased from 20 to 30
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


def handle_already_in_family(file_path):
    # Create a new window to select the family member
    with dpg.window(
        label="Select Family Member",
        width=1920,
        height=1080,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        tag="select_family_member_window",
    ):
        dpg.add_text("Select the family member to store the photo:")

        # Create a new SQLite connection and cursor within this function
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM people")
        family_members = cursor.fetchall()

        # Close the SQLite connection
        conn.close()

        for member_id, member_name in family_members:
            dpg.add_button(
                label=member_name,
                user_data=(member_id, member_name),
                callback=lambda s, a, u: store_photo_in_database(file_path, u[0], u[1]),
            )

        # Close the "select_person_window" window if it exists
        if dpg.does_item_exist("select_person_window"):
            dpg.delete_item("select_person_window")


def store_photo_in_database(file_path, member_id, member_name):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Read the photo data
    with open(file_path, "rb") as file:
        photo_data = file.read()

    # Insert the original photo
    cursor.execute(
        "INSERT INTO photos (person_id, photo) VALUES (?, ?)", (member_id, photo_data)
    )

    # Check if the person already has a profile photo
    cursor.execute(
        "SELECT COUNT(*) FROM photos WHERE person_id = ? AND is_profile_photo = 1",
        (member_id,),
    )
    has_profile_photo = cursor.fetchone()[0] > 0

    if not has_profile_photo:
        # Process the photo to extract the face
        face_photo_data = process_photo_to_extract_face(file_path)
        if face_photo_data:
            # Insert the face photo as the profile photo
            cursor.execute(
                "INSERT INTO photos (person_id, photo, is_profile_photo) VALUES (?, ?, 1)",
                (member_id, face_photo_data),
            )

    conn.commit()
    conn.close()

    # Close the "Select Family Member" window
    dpg.delete_item("select_family_member_window")

    # Close the "New Person" window if it exists
    if dpg.does_item_exist("new_person_window"):
        dpg.delete_item("new_person_window")

    # Show a success message
    success_message = dpg.add_text(
        f"Photo stored for {member_name}.", parent="Primary Window"
    )

    # Remove the success message after 1 second
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message)


def handle_new_person(file_path):
    # Create a new window to enter the person's name and select the role
    with dpg.window(
        label="Enter Details",
        width=1920,
        height=1080,
        no_move=True,
        no_resize=True,
        no_collapse=True,
        no_close=True,
        tag="enter_details_window",
    ):
        dpg.add_text("Enter the details of the new person:")
        dpg.add_input_text(tag="name_input", label="Name")

        dpg.add_text("Select the role:")
        dpg.add_radio_button(
            tag="role_input",
            items=[
                "None",
                "Me",
                "Mom",
                "Dad",
                "Sister",
                "Brother",
            ],
            callback=lambda: toggle_connection_visibility(),
            default_value=None,
        )

        with dpg.collapsing_header(
            label="Connection", tag="connection_header", show=False
        ):
            dpg.add_text("Select the person to whom this person is connected:")

            # Create a new SQLite connection and cursor within this function
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM people")
            people = cursor.fetchall()

            # Close the SQLite connection
            conn.close()

            if people:
                people_names = [f"None"] + [
                    f"{i+1}. {person_name}"
                    for i, (person_id, person_name) in enumerate(people)
                ]
                dpg.add_radio_button(
                    tag="connection_input", items=people_names, default_value=None
                )
            else:
                dpg.add_text("No family members found.")

        dpg.add_button(
            label="Submit",
            callback=lambda: create_new_person_in_database(
                file_path,
                dpg.get_value("name_input"),
                dpg.get_value("role_input"),
                (
                    dpg.get_value("role_input")
                    if dpg.get_value("role_input") == "Me"
                    else (
                        get_person_id_by_name(
                            dpg.get_value("connection_input").split(". ")[1]
                        )
                        if dpg.is_item_shown("connection_header")
                        and dpg.get_value("connection_input")
                        else None
                    )
                ),
            ),
        )

        # Close the "select_person_window" window if it exists
        if dpg.does_item_exist("select_person_window"):
            dpg.delete_item("select_person_window")


def get_person_id_by_name(name):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM people WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def toggle_connection_visibility():
    role = dpg.get_value("role_input")
    if role == "Me" or role == "None":
        dpg.hide_item("connection_header")
    else:
        dpg.show_item("connection_header")


def create_new_person_in_database(file_path, name, role, connected_to):
    # Create a new SQLite connection and cursor within this function
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Insert the new person into the people table with role and connected_to
    cursor.execute(
        "INSERT INTO people (name, role, connected_to) VALUES (?, ?, ?)",
        (name, role, connected_to),
    )
    person_id = cursor.lastrowid

    # Read the photo data
    with open(file_path, "rb") as file:
        photo_data = file.read()

    # Insert the original photo
    cursor.execute(
        "INSERT INTO photos (person_id, photo) VALUES (?, ?)",
        (person_id, photo_data),
    )

    # Process the photo to extract the face
    face_photo_data = process_photo_to_extract_face(file_path)
    if face_photo_data:
        # Insert the face photo as the profile photo
        cursor.execute(
            "INSERT INTO photos (person_id, photo, is_profile_photo) VALUES (?, ?, 1)",
            (person_id, face_photo_data),
        )

    conn.commit()
    conn.close()

    # Close the "Enter Name" window
    dpg.delete_item("enter_name_window")

    # Close the "New Person" window
    dpg.delete_item("new_person_window")

    # Show a success message
    success_message2 = dpg.add_text(
        f"New person '{name}' added successfully!", parent="Primary Window"
    )

    # Close the "enter_details_window" window if it exists
    if dpg.does_item_exist("enter_details_window"):
        dpg.delete_item("enter_details_window")

    # Remove the success message after 1 second
    dpg.split_frame()
    time.sleep(1)
    dpg.delete_item(success_message2)
