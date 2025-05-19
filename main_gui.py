import cv2
import face_recognition
import pickle
import tkinter as tk
from tkinter import ttk, messagebox
from time import strftime

# Import necessary functions from attendance_functions.py
from attendance_system import (
    db_connect,
    live_recognition,
    view_attendance,
    save_attendance_to_excel,
    view_old_records,
)
from staff_enroll import enroll_staff_gui
from enrollment_form import enroll_form_gui


def validate_staff_login(username):
    """Validate the staff username and face recognition."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, encodings FROM staff WHERE name = %s", (username,))
            result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "Username not found!")
            return False

        name, encodings = result
        encodings = pickle.loads(encodings)

        # Open the camera for face recognition
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Camera not accessible!")
            return False

        messagebox.showinfo("Info", "Looking for your face. Please look at the camera.")
        while True:
            ret, frame = cap.read()
            if not ret:
                messagebox.showerror("Error", "Couldn't read from the camera!")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(encodings, face_encoding)
                if True in matches:
                    cap.release()
                    cv2.destroyAllWindows()
                    return True

            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        return False

    except Exception as e:
        messagebox.showerror("Error", f"Error during login: {e}")
        return False

def update_time(label):
    """Update the time label with the current time."""
    current_time = strftime("%Y-%m-%d %H:%M:%S")
    label.config(text=current_time)
    label.after(1000, update_time, label)

def staff_login(window):
    """Handle staff login with username and face recognition."""
    
    login_window = tk.Toplevel(window)
    login_window.title("Staff Login")
    login_window.geometry("400x350")
    login_window.resizable(False, False)
    
    # Load Background Image
    bg_path = "login.jpg"  # Change to your image path
    try:
        bg_image = Image.open(bg_path).resize((400, 350), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(bg_image)
    except:
        bg_image = None  # If image fails to load

    # Background Label
    if bg_image:
        bg_label = tk.Label(login_window, image=bg_image)
        bg_label.image = bg_image
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    else:
        login_window.configure(bg="#1E1E1E")  # Dark background if no image

    # Frame for login UI
    login_frame = tk.Frame(login_window, bg="#333", bd=3, relief="ridge")
    login_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=250)

    tk.Label(login_frame, text="Staff Login", font=("Helvetica", 18, "bold"), bg="#333", fg="white").pack(pady=10)

    # Username Entry
    tk.Label(login_frame, text="Username:", font=("Helvetica", 12), bg="#333", fg="white").pack(anchor="w", padx=20)
    username_entry = tk.Entry(login_frame, font=("Helvetica", 12), bg="#555", fg="white", insertbackground="white")
    username_entry.pack(pady=5, padx=20, fill="x")

    def perform_login():
        username = username_entry.get()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty!")
            return

        if validate_staff_login(username):
            messagebox.showinfo("Success", "Login Successful!")
            login_window.destroy()
            staff_portal(window)
        else:
            messagebox.showerror("Error", "Face recognition failed or user not found!")

    # Buttons Frame
    buttons_frame = tk.Frame(login_frame, bg="#333")
    buttons_frame.pack(pady=20)

    # Login Button
    login_button = tk.Button(
        buttons_frame,
        text="Login",
        font=("Helvetica", 14, "bold"),
        bg="#4CAF50", fg="white",
        activebackground="#388E3C", activeforeground="white",
        relief="flat", cursor="hand2",
        command=perform_login,
    )
    login_button.grid(row=0, column=0, padx=10, pady=5)

    # Hover Effect
    def on_enter(e): login_button.config(bg="black")
    def on_leave(e): login_button.config(bg="#4CAF50")
    login_button.bind("<Enter>", on_enter)
    login_button.bind("<Leave>", on_leave)

    # Cancel Button
    cancel_button = tk.Button(
        buttons_frame,
        text="Cancel",
        font=("Helvetica", 14, "bold"),
        bg="#FF5252", fg="white",
        activebackground="#D32F2F", activeforeground="white",
        relief="flat", cursor="hand2",
        command=login_window.destroy,
    )
    cancel_button.grid(row=0, column=1, padx=10, pady=5)

    def on_enter(e): cancel_button.config(bg="orange")
    def on_leave(e): cancel_button.config(bg="#FF5252")
    cancel_button.bind("<Enter>", on_enter)
    cancel_button.bind("<Leave>", on_leave)

    # Keep window open
    login_window.mainloop()


def staff_portal(window):
    """Staff portal with attendance options."""
    for widget in window.winfo_children():
        widget.destroy()

    tk.Label(
        window,
        text="Staff Portal",
        font=("Helvetica", 20, "bold"),
        bg="#4682b4",
        fg="white",
        pady=10
    ).pack(fill=tk.X)

    buttons_frame = tk.Frame(window, bg="#f0f8ff")
    buttons_frame.pack(pady=20)

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 14), padding=10)

    ttk.Button(
        buttons_frame, text="View Attendance", command=view_attendance
    ).pack(pady=10, fill=tk.X)

    ttk.Button(
        buttons_frame, text="Save Attendance to Excel", command=save_attendance_to_excel
    ).pack(pady=10, fill=tk.X)

    ttk.Button(
        buttons_frame, text="View Old Records", command=view_old_records
    ).pack(pady=10, fill=tk.X)

    ttk.Button(
        buttons_frame, text="Logout", command=lambda: main_page(window)
    ).pack(pady=10, fill=tk.X)
    tk.Button(
        buttons_frame,
        text="New Staff?",
        fg="white",
        bg="#1976d2",
        relief="flat",
        bd=5,
        font=("Arial Black", 14),
        command=lambda: [window.destroy(), enroll_staff_gui()],
    ).pack(pady=30, fill=tk.X , padx=35)
    tk.Button(
        buttons_frame,
        text="New Student?",
        fg="white",
        bg="#1976d2",
        relief="flat",
        bd=5,
        font=("Arial Black", 14),
        command=lambda: [window.destroy(), enroll_form_gui()],
    ).pack(pady=30, fill=tk.X , padx=35)

import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk  # For background image support
import time
import webview  # Used to embed the chatbot link inside Tkinter

CHATBOT_URL = "https://www.chatbase.co/chatbot-iframe/8bFdTCDlW19359JrSBmxF"  # Replace with your actual chatbot link

def open_chatbot():
    """Opens the chatbot inside a Tkinter window using WebView."""
    webview.create_window("Chatbot", CHATBOT_URL, width=400, height=500)
    webview.start()

def update_time(label):
    """Update time dynamically with date."""
    current_time = time.strftime("%I:%M:%S %p")  # 12-hour format with AM/PM
    current_date = time.strftime("%A, %B %d, %Y")  # Day, Month Date, Year
    label.config(text=f"{current_date}\n{current_time}")
    label.after(1000, update_time, label)  # Update every second

# Store the original image globally
original_image = None

def main_page(window):
    """Main page with options for students and staff."""
    global original_image  # Keep image reference persistent

    for widget in window.winfo_children():
        widget.destroy()

    window.title("Face Attendance System")
    window.geometry("1300x1000")  # Default size
    window.resizable(True, True)  # Allow manual resizing

    # Load background image only once
    if original_image is None:
        image_path = "back.jpg"
        try:
            original_image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Error: Image '{image_path}' not found!")
            return

    # Resize image to fit the initial window size
    resized_image = original_image.resize((1400, 1000), Image.LANCZOS)
    bg_image = ImageTk.PhotoImage(resized_image)

    # Set the background label
    bg_label = Label(window, image=bg_image)
    bg_label.image = bg_image  # Prevent garbage collection
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Gradient Header
    header_frame = tk.Canvas(window, height=80, width=500, bg="#4682b4", highlightthickness=0)
    header_frame.pack(pady=40, padx=30)

    header_frame.create_rectangle(0, 0, 500, 80, fill="#4682b4", outline="")
    header_frame.create_text(
        250, 40, text="Face Recognition Attendance", font=("Stencil", 20, "bold"), fill="white"
    )

    # Time & Date Label
    time_label = tk.Label(window, font=("Stencil", 19, "bold"), bg="#e3f2fd", fg="red")
    time_label.pack(pady=10)
    update_time(time_label)

    # Buttons Frame
    buttons_frame = tk.Frame(window, bg="#e3f2fd")
    buttons_frame.pack(pady=30)

    def create_button(text, command):
        """Helper function to create stylish buttons"""
        btn = tk.Button(
            buttons_frame,
            text=text,
            font=("Algerian", 23, "bold"),
            fg="orange",
            bg="#1976d2",
            relief="groove",
            bd=3,
            padx=10,
            pady=8,
            width=50,
            height=2,
            cursor="hand2",
            activebackground="#1565c0",
            activeforeground="white",
            command=command
        )
        btn.pack(pady=10, fill=tk.X, padx=30)
        return btn

    # Buttons with proper command functions
    create_button("▶ Start Live Recognition", lambda: live_recognition())
    create_button("🔑 Staff Login", lambda: staff_login(window))
    create_button("❌ Exit", lambda: window.quit())
    

    try:
        chatbot_icon = Image.open("chat.png")  # Use your chatbot icon image
        chatbot_icon = chatbot_icon.resize((65, 65), Image.LANCZOS)
        chatbot_icon = ImageTk.PhotoImage(chatbot_icon)

        chatbot_button = tk.Button(
            window,
            image=chatbot_icon,
            bg="#e3f2fd",
            bd=0,
            cursor="hand2",
            command=open_chatbot
        )
        chatbot_button.image = chatbot_icon  # Prevent garbage collection
        chatbot_button.pack(side="right", padx=20)
    except FileNotFoundError:
        print("Chatbot icon not found! Make sure 'chat.png' exists.")

    # Footer
    footer_frame = tk.Frame(window, bg="#e3f2fd", height=60)
    footer_frame.pack(side="bottom", fill="x")

    footer_label = tk.Label(
        footer_frame, text="©  2025   Face   Attendance   System ", font=("Showcard Gothic", 10, "italic"), bg="#e3f2fd", fg="#555"
    )
    footer_label.pack(side="left", padx=10)
    
# Sample window execution
if __name__ == "__main__":
    window = tk.Tk()
    main_page(window)
    window.mainloop()
