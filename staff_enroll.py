import tkinter as tk
from tkinter import ttk, messagebox
import os
import cv2
import face_recognition
import mysql.connector
import pickle

# Database connection
def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Update with your MySQL root password
        database="attendance_system"
    )
#from main_gui import staff_portal

def capture_and_encode_staff(staff_data):
    staff_id = staff_data["staff_id"]
    output_dir = os.path.join("photos", staff_id)
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

        # Generate face encoding
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encoding = face_recognition.face_encodings(rgb_frame)
        if encoding:
            encodings.append(encoding[0])
        count += 1

    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO staff (staff_id, name, department, phone, email, encodings)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        staff_data["staff_id"],
                        staff_data["name"],
                        staff_data["department"],
                        staff_data["phone"],
                        staff_data["email"],
                        pickle.dumps(encodings),
                    ),
                )
                conn.commit()
            messagebox.showinfo("Info", "Staff enrolled and photos captured!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save staff to database: {e}")
    else:
        messagebox.showerror("Error", "Failed to generate face encodings!")

def enroll_staff_gui():
    def save_staff():
        staff_data = {
            "staff_id": id_entry.get(),
            "name": name_entry.get(),
            "department": dept_entry.get(),
            "phone": phone_entry.get(),
            "email": email_entry.get(),
        }

        if not all(staff_data.values()):
            messagebox.showerror("Error", "All fields must be filled!")
            return

        capture_and_encode_staff(staff_data)

    # Hover effect for buttons
    def on_enter(e):
        e.widget.config(style="Hover.TButton")

    def on_leave(e):
        e.widget.config(style="TButton")

    # GUI Window
    window = tk.Tk()
    window.title("Enroll Staff")
    window.geometry("500x650")
    window.configure(bg="#2C3E50")  # Dark background

    # Styling
    style = ttk.Style()
    style.configure("TButton", font=("Arial Black", 12), padding=10, background="#3498DB", foreground="white")
    style.configure("Hover.TButton", font=("Arial Black", 12,"bold"), padding=10, background="#2C3E50", foreground="blue")
    style.configure("TLabel", font=("Arial Black", 12), background="#2C3E50", foreground="white")
    style.configure("TEntry", font=("Arial Black", 12), padding=5)

    # Title Label
    ttk.Label(window, text="Enroll New Staff", font=("Arial Black", 18, "bold"), background="#2C3E50", foreground="white").pack(pady=20)

    # Form Fields
    frame = ttk.Frame(window)
    frame.pack(pady=10)

    labels = ["Staff ID:", "Name:", "Department:", "Phone:", "Email:"]
    entries = []

    for label in labels:
        ttk.Label(frame, text=label).pack(anchor="w", padx=20, pady=5)
        entry = ttk.Entry(frame, width=40)
        entry.pack(padx=20, pady=5)
        entries.append(entry)

    id_entry, name_entry, dept_entry, phone_entry, email_entry = entries

    # Enroll Button
    enroll_btn = ttk.Button(window, text="Enroll Staff", command=save_staff, style="TButton")
    enroll_btn.pack(pady=20)

    # Adding hover effect
    enroll_btn.bind("<Enter>", on_enter)
    enroll_btn.bind("<Leave>", on_leave)

    window.mainloop()

if __name__ == "__main__":
    enroll_staff_gui()
