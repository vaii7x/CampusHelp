-- CampusHelp database schema
-- Creates an empty database with the current table structure.
-- No student records or private data are included.
-- Run this against a fresh database; it does not delete existing data.

CREATE DATABASE IF NOT EXISTS CampusHelp
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE CampusHelp;

CREATE TABLE IF NOT EXISTS students (
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    department VARCHAR(100) DEFAULT NULL,
    semester INT DEFAULT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    reg_no VARCHAR(30) NOT NULL,
    PRIMARY KEY (reg_no),
    UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS timetables (
    timetable_id INT NOT NULL AUTO_INCREMENT,
    image_path VARCHAR(500) DEFAULT NULL,
    uploaded_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('uploaded','processing','review_required','verified','failed') DEFAULT 'uploaded',
    reg_no VARCHAR(30) NOT NULL,
    PRIMARY KEY (timetable_id),
    KEY idx_timetables_reg_no (reg_no),
    CONSTRAINT fk_timetables_reg_no
        FOREIGN KEY (reg_no) REFERENCES students (reg_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS classes (
    class_id INT NOT NULL AUTO_INCREMENT,
    timetable_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    subject VARCHAR(100) DEFAULT NULL,
    PRIMARY KEY (class_id),
    KEY idx_classes_schedule (timetable_id, day_of_week, start_time),
    CONSTRAINT classes_ibfk_1
        FOREIGN KEY (timetable_id) REFERENCES timetables (timetable_id)
        ON DELETE CASCADE,
    CONSTRAINT classes_chk_1 CHECK (day_of_week BETWEEN 1 AND 7),
    CONSTRAINT classes_chk_2 CHECK (start_time < end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT NOT NULL AUTO_INCREMENT,
    created_by VARCHAR(30) NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    location VARCHAR(200) NOT NULL,
    task_date DATE NOT NULL,
    start_time TIME DEFAULT NULL,
    end_time TIME DEFAULT NULL,
    status ENUM('open','assigned','in_progress','completed','cancelled') DEFAULT 'open',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id),
    KEY idx_tasks_schedule (task_date, status),
    KEY idx_tasks_created_by (created_by),
    CONSTRAINT fk_tasks_created_by_reg_no
        FOREIGN KEY (created_by) REFERENCES students (reg_no),
    CONSTRAINT tasks_chk_1 CHECK (start_time < end_time),
    CONSTRAINT tasks_chk_2 CHECK ((start_time >= '08:00:00' AND end_time <= '13:00:00'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS task_requests (
    request_id INT NOT NULL AUTO_INCREMENT,
    task_id INT NOT NULL,
    requested_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','accepted','declined','withdrawn') DEFAULT 'pending',
    reg_no VARCHAR(30) NOT NULL,
    PRIMARY KEY (request_id),
    UNIQUE KEY task_id (task_id),
    KEY idx_task_requests_reg_no (reg_no),
    CONSTRAINT fk_task_requests_reg_no
        FOREIGN KEY (reg_no) REFERENCES students (reg_no),
    CONSTRAINT task_requests_ibfk_1
        FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id INT NOT NULL AUTO_INCREMENT,
    task_id INT NOT NULL,
    assigned_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    status ENUM('assigned','in_progress','completed','cancelled') DEFAULT 'assigned',
    reg_no VARCHAR(30) NOT NULL,
    PRIMARY KEY (assignment_id),
    UNIQUE KEY task_id (task_id),
    KEY idx_assignments_reg_no (reg_no),
    CONSTRAINT assignments_ibfk_1
        FOREIGN KEY (task_id) REFERENCES tasks (task_id),
    CONSTRAINT fk_assignments_reg_no
        FOREIGN KEY (reg_no) REFERENCES students (reg_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS availability (
    availability_id INT NOT NULL AUTO_INCREMENT,
    available_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available TINYINT(1) DEFAULT 1,
    source ENUM('timetable','manual') DEFAULT 'timetable',
    reg_no VARCHAR(30) NOT NULL,
    PRIMARY KEY (availability_id),
    KEY idx_availability_search (available_date, is_available, start_time, end_time),
    KEY idx_availability_reg_no (reg_no),
    CONSTRAINT fk_availability_reg_no
        FOREIGN KEY (reg_no) REFERENCES students (reg_no) ON DELETE CASCADE,
    CONSTRAINT availability_chk_1 CHECK (start_time < end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
