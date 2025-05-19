# Face_Attendance_System
A smart Python-based Face Recognition Attendance System using OpenCV. It marks In-Time and Out-Time in Excel, recognizes faces from a webcam, and prevents duplicate entries. Easily customizable and optionally supports Twilio SMS alerts. Ideal for schools, colleges, and workplaces.


# Face Recognition Attendance System 🎓📸

This is an advanced Face Recognition-based Attendance System built with **Python**, **OpenCV**, and **MySQL**. It automatically detects and identifies faces via a webcam, then marks **In-Time** and **Out-Time** attendance into an Excel sheet. Designed for schools, colleges, and workplaces.

---

## 🚀 Features

- 🔐 **Face Detection and Recognition** using OpenCV and `face_recognition` library
- 🕒 Records **In-Time** and **Out-Time** for each person
- 🧠 **Trained Dataset** of known faces
- 🧾 Stores attendance in an **Excel sheet**
- 🔁 Avoids **duplicate entries** for the same person on the same day
- 💬 [Optional] **Twilio SMS Alerts** to notify on attendance
- 💽 **MySQL backend** for storing user data (configurable)

---

## 🛠️ Tech Stack

- **Python**: Core programming language
- **OpenCV**: Real-time image processing
- **face_recognition**: For accurate facial feature detection
- **Pandas**: Excel attendance sheet management
- **MySQL**: Backend database for storing user metadata
- **Tkinter**: For GUI (if included)
- **Twilio**: [Optional] For sending SMS notifications

---
