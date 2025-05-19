import cv2
import face_recognition
import mysql.connector
import pickle
import tkinter as tk
from tkinter import messagebox,ttk
import pyttsx3
from datetime import datetime

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 150)

def db_connect():
    """Connect to MySQL database."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Update with your MySQL root password
        database="attendance_system"
    )

def live_recognition():
    """Start live face recognition with attendance marking."""
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, name, encodings FROM students")
        data = cursor.fetchall()
        known_faces = {
            row[0]: {"name": row[1], "encodings": pickle.loads(row[2])} for row in data
        }

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Camera not accessible!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            match_found = False
            for student_id, details in known_faces.items():
                matches = face_recognition.compare_faces(
                    details["encodings"], face_encoding, tolerance=0.5
                )
                if any(matches):
                    now = datetime.now()
                    current_time = now.strftime("%H:%M:%S")
                    date = now.strftime("%Y-%m-%d")
                    current_hour = int(now.strftime("%H"))
                    current_minute = int(now.strftime("%M"))

                    with db_connect() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT in_time, out_time, in_status, out_status, status FROM attendance WHERE student_id=%s AND date=%s",
                            (student_id, date),
                        )
                        attendance_record = cursor.fetchone()

                        if attendance_record:
                            # Existing attendance record found
                            in_time, out_time, in_status, out_status, status = attendance_record
                            if not in_time:
                                message = f"ID {student_id} - Cannot Mark Out (No In Time)"
                            elif out_time:  # If out_time is already marked
                                message = f"ID {student_id} - Already Marked Out"
                            else:
                                # Update based on the time for out_status
                                if 16 <= current_hour < 19:  # 4:00 PM to 7:00 PM
                                    new_out_status = "Correct Time"
                                    cursor.execute(
                                        """
                                        UPDATE attendance 
                                        SET out_time = %s, out_status = %s 
                                        WHERE student_id = %s AND date = %s
                                        """,
                                        (current_time, new_out_status, student_id, date),
                                    )
                                    conn.commit()
                                    message = f"ID {student_id} - Out Time Marked"
                                elif 15 <= current_hour < 16:  # 3:00 PM to 4:00 PM
                                    new_out_status = "Permission"
                                    cursor.execute(
                                        """
                                        UPDATE attendance
                                        SET out_time = %s, out_status = %s
                                        WHERE student_id = %s AND date = %s
                                        """,
                                        (current_time, new_out_status, student_id, date),
                                    )
                                    conn.commit()
                                    message = f"ID {student_id} - Permission Granted"
                                elif 19 <= current_hour < 20:  # 7:00 PM to 8:00 PM
                                    new_out_status = "Over Time"
                                    cursor.execute(
                                        """
                                        UPDATE attendance
                                        SET out_time = %s, out_status = %s
                                        WHERE student_id = %s AND date = %s
                                        """,
                                        (current_time, new_out_status, student_id, date),
                                    )
                                    conn.commit()
                                    message = f"ID {student_id} - Over Time Marked"
                                else:
                                    message = f"ID {student_id} - Already Marked"
                        else:
                            # New attendance entry
                            if 7 <= current_hour < 8:
                                in_status = "Early Present"
                            elif 8 <= current_hour < 10:
                                in_status = "Present"
                            elif 10 <= current_hour < 11:
                                in_status = "Late Present"
                            else:
                                in_status = None

                            if in_status:
                                cursor.execute(
                                    """
                                    INSERT INTO attendance (student_id, date, in_time, in_status, status)
                                    VALUES (%s, %s, %s, %s, %s)
                                    """,
                                    (student_id, date, current_time, in_status, "Present"),
                                )
                                conn.commit()
                                message = f"ID {student_id} - {in_status} Marked"
                            else:
                                message = f"ID {student_id} - No Attendance Marked (Invalid Time)"

                    # Display the bounding box and status message
                    top, right, bottom, left = face_location
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        message,
                        (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    engine.say(message)
                    engine.runAndWait()
                    match_found = True
                    break

            if not match_found:
                # Display and announce unknown face
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(
                    frame,
                    "Unknown Face",
                    (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )
                engine.say("Unknown Person Detected!")
                engine.runAndWait()

        cv2.imshow("Live Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

def view_attendance():
    """View all attendance records."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    students.student_id, 
                    students.name, 
                    students.sex, 
                    students.course, 
                    students.department,
                    students.phone,
                    attendance.date, 
                    TIME_FORMAT(attendance.in_time, '%H:%i:%s') AS in_time, 
                    TIME_FORMAT(attendance.out_time, '%H:%i:%s') AS out_time, 
                    attendance.in_status, 
                    attendance.out_status, 
                    attendance.status 
                FROM attendance
                INNER JOIN students ON attendance.student_id = students.student_id
                ORDER BY attendance.date DESC, attendance.in_time ASC
            """)
            data = cursor.fetchall()

        # Display the retrieved data in a new window
        if data:
            display_records(data, "All Attendance Records")
        else:
            messagebox.showinfo("No Records Found", "No attendance records available to display.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while fetching attendance data: {e}")

import tkinter as tk
from tkinter import ttk
from twilio.rest import Client

# Twilio Configuration
from datetime import datetime
from twilio.rest import Client

# Twilio Configuration
TWILIO_ACCOUNT_SID = "ACe8ac415f362f609e43f4d77d8e4f3eda"
TWILIO_AUTH_TOKEN = "76581c3071877b7e85103772bbdea5b0"
TWILIO_PHONE_NUMBER = "+17159727054"
TWIML_URL = "https://handler.twilio.com/twiml/EH512b4373965f86cff9a2d2fb0b4078e6"

def send_sms(to_number, message):
    """Send an SMS to a specific phone number using Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    if not to_number.startswith("+91"):
        to_number = "+91" + to_number

    try:
        client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message
        )
        print(f"Message sent to {to_number}")
    except Exception as e:
        print(f"Failed to send SMS to {to_number}: {e}")

def send_call(to_number):
    """Initiate a call to the given phone number using Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    if not to_number.startswith("+91"):
        to_number = "+91" + to_number

    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=TWIML_URL
        )
        print(f"Call initiated! Call SID: {call.sid}")
    except Exception as e:
        print(f"Failed to initiate call to {to_number}: {e}")      

def send_absentee_sms(data):
    """Send SMS and call only to students who were marked absent today."""
    
    today_date = datetime.now().strftime("%Y-%m-%d")  # Get today's date in YYYY-MM-DD format

    for row in data:
        phone_number = row[5]  # Adjust index as needed
        student_name = row[1]  # Student's Name
        status = row[11]       # Attendance Status
        date_marked = row[6]  # Date of Attendance (ensure this column exists)

        # Check if student is absent today
        if status == "Absent": #and date_marked == today_date:
            message = (
                f"Dear {student_name},\n"
                f"Our records indicate you were marked absent today ({date_marked}). "
                f"Please ensure your attendance in future sessions. Contact admin for queries."
            )

            if phone_number:
                send_sms(phone_number, message)  # Send SMS
                send_call(phone_number)         # Initiate call


def display_records(data, title):
    """Display attendance records and send absentee SMS automatically."""
    # Automatically send SMS to absentees when this function is called
    send_absentee_sms(data)

    # Create the attendance display window
    attendance_window = tk.Toplevel()
    attendance_window.title(title)
    attendance_window.geometry("1200x600")

    tk.Label(
        attendance_window,
        text=title,
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    # Define columns for the table
    columns = (
        "Student ID", "Name", "Sex", "Course", "Department",
        "Phone Number", "Date", "In Time", "Out Time", 
        "In Status", "Out Status", "Attendance Status"
    )

    # Create Treeview for tabular display
    tree = ttk.Treeview(attendance_window, columns=columns, show="headings", height=20)
    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    # Configure column widths and headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")

    # Populate data into the table
    for row in data:
        row = tuple(value if value is not None else "N/A" for value in row)  # Replace None with "N/A"
        tree.insert("", "end", values=row)

    # Add a scroll bar for better navigation
    scrollbar = ttk.Scrollbar(attendance_window, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Add a close button
    tk.Button(
        attendance_window, 
        text="Close", 
        command=attendance_window.destroy, 
        font=("Arial", 12), 
        bg="#f54242", 
        fg="white"
    ).pack(pady=10)

import os
from openpyxl import Workbook

def save_attendance_to_excel():
    """Save the current attendance records to an Excel file with in_status, out_status, and main_status."""
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        current_hour = int(now.strftime("%H"))

        # Automatically close attendance after 8 PM (customize as needed)
        if current_hour >= 11:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Identify students without attendance records for today
                cursor.execute("""
                    SELECT student_id 
                    FROM students 
                    WHERE student_id NOT IN (
                        SELECT student_id 
                        FROM attendance 
                        WHERE date = %s
                    )
                """, (date_str,))
                absent_students = cursor.fetchall()

                # Insert "Absent" status for students without attendance
                if absent_students:
                    for student_id in absent_students:
                        cursor.execute("""
                            INSERT INTO attendance (student_id, date, in_status, out_status, status)
                            VALUES (%s, %s, 'Absent', 'Absent', 'Absent')
                        """, (student_id[0], date_str))
                else:
                    # If no attendance exists, mark all students as "Absent"
                    cursor.execute("""
                        INSERT INTO attendance (student_id, date, in_status, out_status, status)
                        SELECT student_id, %s, 'Absent', 'Absent', 'Absent' 
                        FROM students
                    """, (date_str,))

                conn.commit()

        # Fetch attendance records with in_status, out_status, and main_status
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    students.student_id, 
                    students.name, 
                    students.sex, 
                    students.course, 
                    students.department, 
                    %s AS date, 
                    COALESCE(attendance.in_time, 'N/A') AS in_time, 
                    COALESCE(attendance.out_time, 'N/A') AS out_time, 
                    COALESCE(attendance.in_status, 'Absent') AS in_status, 
                    COALESCE(attendance.out_status, 'Absent') AS out_status, 
                    COALESCE(attendance.status, 'Absent') AS status
                FROM students
                LEFT JOIN attendance 
                ON students.student_id = attendance.student_id 
                AND attendance.date = %s
                ORDER BY students.student_id
            """, (date_str, date_str))
            data = cursor.fetchall()

        # Save attendance data to an Excel file
        file_name = f"attendance_{date_str}.xlsx"
        file_path = os.path.join(os.getcwd(), "attendance_records", file_name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create an Excel workbook and write data
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Records"

        # Updated headers to include in_status, out_status, and main_status
        headers = [
            "Student ID", "Name", "Sex", "Course", "Department", 
            "Date", "In Time", "Out Time", "In Status", "Out Status", "Main Status"
        ]
        ws.append(headers)

        for row in data:
            ws.append(row)

        wb.save(file_path)

        # Log file creation in the database
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO old_attendance_records (record_date, file_path)
                VALUES (%s, %s)
            """, (date_str, file_path))
            conn.commit()

        messagebox.showinfo("Success", f"Attendance saved to file: {file_name}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving attendance to Excel: {e}")

def view_old_records():
    """View and generate attendance records for a selected date."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT DATE(date) AS record_date 
                FROM attendance 
                ORDER BY record_date
            """)
            dates = cursor.fetchall()

        if not dates:
            messagebox.showinfo("Info", "No attendance records available.")
            return

        # Create a new window to display available dates
        old_records_window = tk.Toplevel()
        old_records_window.title("View Attendance Records by Date")
        old_records_window.geometry("400x400")

        tk.Label(
            old_records_window, 
            text="Select a Date to View Attendance", 
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Create a listbox to display available dates
        listbox = tk.Listbox(old_records_window, font=("Arial", 12))
        listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        available_dates = [date[0].strftime("%Y-%m-%d") for date in dates]
        for date_str in available_dates:
            listbox.insert(tk.END, date_str)

        def generate_and_open_excel():
            """Generate and open attendance records for the selected date."""
            selected_date = listbox.get(tk.ACTIVE)
            if not selected_date:
                messagebox.showwarning("Warning", "Please select a date.")
                return

            try:
                # Query attendance records for the selected date
                with db_connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT students.student_id, students.name, students.sex, students.course, 
                               students.department, attendance.date, 
                               COALESCE(attendance.in_time, 'N/A') AS in_time, 
                               COALESCE(attendance.out_time, 'N/A') AS out_time, 
                               COALESCE(attendance.in_status, 'Absent') AS in_status, 
                               COALESCE(attendance.out_status, 'Absent') AS out_status, 
                               COALESCE(attendance.status, 'Absent') AS status
                        FROM students
                        LEFT JOIN attendance 
                        ON students.student_id = attendance.student_id 
                        AND DATE(attendance.date) = %s
                    """, (selected_date,))
                    data = cursor.fetchall()

                # If no attendance data exists for the selected date, mark all students as absent
                if not data:
                    with db_connect() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT students.student_id, students.name, students.sex, students.course, 
                                   students.department, %s AS date, 
                                   'N/A' AS in_time, 'N/A' AS out_time, 
                                   'Absent' AS in_status, 'Absent' AS out_status, 'Absent' AS status
                            FROM students
                        """, (selected_date,))
                        data = cursor.fetchall()

                # Generate Excel file for the selected date
                file_name = f"attendance_{selected_date}.xlsx"
                file_path = os.path.join(os.getcwd(), "attendance_records", file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                wb = Workbook()
                ws = wb.active
                ws.title = f"Attendance {selected_date}"

                # Updated headers to include in_status, out_status, and main_status
                headers = [
                    "Student ID", "Name", "Sex", "Course", "Department", 
                    "Date", "In Time", "Out Time", "In Status", "Out Status", "Main Status"
                ]
                ws.append(headers)

                for row in data:
                    ws.append(row)

                wb.save(file_path)

                # Open the generated Excel file
                if os.path.exists(file_path):
                    os.startfile(file_path)
                else:
                    messagebox.showerror("Error", "Failed to generate the attendance file.")

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

        tk.Button(
            old_records_window, 
            text="View", 
            command=generate_and_open_excel, 
            font=("Arial", 12)
        ).pack(pady=10)
        tk.Button(
            old_records_window, 
            text="Close", 
            command=old_records_window.destroy, 
            font=("Arial", 12)
        ).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")