import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage, Label, Entry, Button, Frame, OptionMenu, StringVar
import os
import cv2
import face_recognition
import mysql.connector
import pickle
from PIL import Image, ImageTk

# Database connection
def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Update with your MySQL password
        database="attendance_system"
    )

# Delete student function
def delete_student(delete_entry):
    student_id = delete_entry.get()
    if not student_id:
        messagebox.showerror("Error", "Please enter a Student ID to delete.")
        return

    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student:
                messagebox.showerror("Error", "Student ID not found!")
                return
            
            cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
            conn.commit()

        # Remove student photos
        student_photo_dir = os.path.join("photos", student_id)
        if os.path.exists(student_photo_dir):
            for file in os.listdir(student_photo_dir):
                os.remove(os.path.join(student_photo_dir, file))
            os.rmdir(student_photo_dir)

        messagebox.showinfo("Success", f"Student record for ID '{student_id}' deleted successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete student: {e}")

# Capture and encode face
def capture_and_encode(student_data):
    student_id = student_data["student_id"]
    output_dir = os.path.join("photos", student_id)
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Camera not accessible!")
        return

    messagebox.showinfo("Info", "Capturing 30 photos. Press 'q' to quit early.")
    count = 0
    encodings = []

    while count < 30:
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Couldn't read from camera!")
            break
        
        cv2.imshow("Capturing Faces", frame)
        key = cv2.waitKey(100) & 0xFF
        if key == ord('q'):
            break

        file_path = os.path.join(output_dir, f"photo{count + 1}.jpg")
        cv2.imwrite(file_path, frame)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encoding = face_recognition.face_encodings(rgb_frame)
        if encoding:
            encodings.append(encoding[0])
        count += 1
    
    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO students (name, student_id, sex, course, department, phone, email, address, encodings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    student_data["name"],
                    student_id,
                    student_data["sex"],
                    student_data["course"],
                    student_data["department"],
                    student_data["phone"],
                    student_data["email"],
                    student_data["address"],
                    pickle.dumps(encodings),
                ),
            )
            conn.commit()
        messagebox.showinfo("Info", "Student enrolled and photos captured!")
    else:
        messagebox.showerror("Error", "Failed to generate encodings!")

# GUI Form
def enroll_form_gui():
    def save_student():
        student_data = {
            "name": name_entry.get(),
            "student_id": id_entry.get(),
            "sex": sex_var.get(),
            "course": course_entry.get(),
            "department": dept_entry.get(),
            "phone": phone_entry.get(),
            "email": email_entry.get(),
            "address": address_entry.get(),
        }

        if not all(student_data.values()):
            messagebox.showerror("Error", "All fields must be filled!")
            return

        capture_and_encode(student_data)

    # Create the main window
    window = tk.Tk()
    window.title("Student Enrollment System")
    window.geometry("700x800")  # Adjusted window size

    # Background Image
    bg_image = Image.open("back.jpg")  # Make sure you have a background image
    bg_image = bg_image.resize((700, 800), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)

    bg_label = Label(window, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

    # Main Frame with rounded corners
    frame = Frame(window, bg="white", bd=5, relief="ridge")
    frame.place(relx=0.5, rely=0.05, relwidth=0.9, relheight=0.9, anchor="n")

    Label(frame, text="Enroll New Student", font=("Arial", 18, "bold"), bg="white", fg="#333").pack(pady=10)

    # Entry Fields with stylish design
    def create_label_entry(text):
        Label(frame, text=text, font=("Arial", 12, "bold"), bg="white").pack(pady=5)
        entry = Entry(frame, font=("Arial", 12), bg="#f0f0f0", bd=2, relief="flat")
        entry.pack(ipady=5, padx=20, fill="x")
        return entry

    name_entry = create_label_entry("Name:")
    id_entry = create_label_entry("Student ID:")
    sex_var = StringVar(value="Male")
    Label(frame, text="Sex:", font=("Arial", 12, "bold"), bg="white").pack(pady=5)
    sex_dropdown = OptionMenu(frame, sex_var, "Male", "Female", "Other")
    sex_dropdown.pack(pady=5)

    course_entry = create_label_entry("Course:")
    dept_entry = create_label_entry("Department:")
    phone_entry = create_label_entry("Phone:")
    email_entry = create_label_entry("Email:")
    address_entry = create_label_entry("Address:")

    # ttk Style for Buttons
    style = ttk.Style()
    style.configure("TButton", font=("Arial Black", 12), padding=10, relief="flat", background="white",foreground="white")
    style.map("TButton", background=[("active", "blue")], foreground=[("active", "blue")])

    # Enroll Button
    enroll_button = ttk.Button(frame, text="Enroll", command=save_student, style="TButton")
    enroll_button.pack(pady=15, ipadx=20)

    # Delete Section
    Label(frame, text="Delete Student Record", font=("Arial", 16, "bold"), bg="white", fg="#333").pack(pady=10)
    delete_entry = Entry(frame, font=("Arial", 12), bg="#f0f0f0", bd=2, relief="flat")
    delete_entry.pack(ipady=5, padx=20, fill="x", pady=5)

    delete_button = Button(frame, text="Delete", font=("Arial", 14, "bold"), command=lambda: delete_student(delete_entry), bg="red", fg="white", relief="raised", borderwidth=3)
    delete_button.pack(pady=10, ipadx=20)

    window.mainloop()

if __name__ == "__main__":
    enroll_form_gui()
