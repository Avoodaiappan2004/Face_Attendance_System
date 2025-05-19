CREATE DATABASE attendance_system;
USE attendance_system;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    sex ENUM('Male', 'Female', 'Other') NOT NULL,
    course VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(255),
    address TEXT,
    photo_path VARCHAR(255),
    encodings MEDIUMBLOB NOT NULL
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    in_time TIME NULL,
    out_time TIME NULL,
    attendance_status ENUM('Present', 'Absent') NOT NULL, -- Main attendance status
    in_status ENUM('Early', 'Late', 'Correct time') DEFAULT 'Correct time', -- In-time status
    out_status ENUM('Permission', 'Overtime', 'Correct time') DEFAULT 'Correct time', -- Out-time status
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

ALTER TABLE attendance CHANGE attendance_status status ENUM('Present', 'Absent') NOT NULL;


CREATE TABLE old_attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_date DATE NOT NULL,
    file_path VARCHAR(255) NOT NULL
);

CREATE TABLE staff (
    staff_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) NOT NULL,
    encodings LONGBLOB NOT NULL
);
