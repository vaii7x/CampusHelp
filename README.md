# CampusHelp — Campus Parcel Pickup Coordination System

CampusHelp is a student-focused application designed to simplify parcel pickup coordination within a university campus. It allows students to post pickup requests and coordinate with fellow students who may have free time between laboratory sessions.

The project combines a Python backend, a MySQL relational database, and a Flask-based web interface to provide a centralized platform for student coordination.

**Repository:** https://github.com/vaii7x/CampusHelp

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [System Workflow](#system-workflow)
- [Scheduling and Availability Rules](#scheduling-and-availability-rules)
- [Database Design](#database-design)
- [Database Normalization](#database-normalization)
- [User Interface](#user-interface)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Conclusion](#conclusion)

## Problem Statement

Students may be unable to collect parcels from campus reception points because of laboratory sessions, academic commitments, and conflicting schedules. Informal coordination can make it difficult to identify another student who is available to help.

CampusHelp addresses this problem by providing a centralized system for creating pickup tasks, recording student requests, managing laboratory schedules, and organizing task assignments.

## Objectives

- Provide a centralized platform for parcel pickup coordination.
- Maintain student information in a relational database.
- Allow students to record laboratory schedules.
- Identify potential free intervals based on defined scheduling rules.
- Support the creation and viewing of parcel pickup tasks.
- Record pickup requests and assignments.
- Provide a user-friendly web interface for accessing application features.
- Maintain data consistency through relational database design.

## Key Features

### Student Management
- Student registration and login.
- Student profile management.
- Storage of student details in MySQL.
- Password hashing and verification.

### Timetable Management
- Entry of laboratory sessions.
- Storage of day, subject, start time, and end time.
- Retrieval of saved laboratory schedules.
- Support for timetable-based availability calculations.

### Parcel Task Management
- Creation of parcel pickup tasks.
- Viewing open tasks.
- Submission of pickup requests.
- Tracking of tasks created by a student.
- Storage of task and request information.

### Availability Calculation
- Defined pickup window from 8:00 AM to 1:00 PM.
- Minimum continuous pickup duration of 15 minutes.
- Treatment of gaps of 10 minutes or less between consecutive labs as unavailable.
- Identification of qualifying free intervals from laboratory schedules.

### Web Interface
- Landing page.
- Login and registration pages.
- Student dashboard.
- Timetable management page.
- Parcel tasks page.
- Student profile page.

*Feature note: The availability rules describe the project's intended scheduling logic. Automatic eligibility filtering and assignment through the web interface should be considered implemented only after integration and testing.*

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and backend functionality |
| Flask | Web routes, requests, sessions, and page rendering |
| HTML | Web page structure |
| CSS | Styling and responsive layouts |
| JavaScript | Client-side interactions |
| MySQL | Relational database |
| MySQL Connector/Python | Database connectivity |
| Werkzeug | Password hashing and verification |
| Python `hashlib` | Verification of the existing CLI's PBKDF2 password format |
| `python-dotenv` | Loading local environment variables |
| Visual Studio Code | Development environment |
| Git and GitHub | Version control and source-code hosting |

## System Architecture

CampusHelp follows a layered architecture.

1. **Presentation layer:** HTML, CSS, and JavaScript provide the web interface.
2. **Application layer:** Flask processes HTTP requests, handles routes, manages sessions, and validates form submissions.
3. **Business logic layer:** Python code manages timetable operations, availability calculations, and parcel task operations.
4. **Data layer:** MySQL stores student details, timetables, laboratory sessions, tasks, requests, assignments, and availability records.

### Architecture Overview

```text
Student
   |
   v
Web Browser
HTML + CSS + JavaScript
   |
   v
Flask Application
Routes + Authentication + Sessions
   |
   v
Python Application Logic
Timetable + Availability + Tasks
   |
   v
MySQL Database
Students + Classes + Tasks + Requests
```

The Flask application currently contains database queries of its own. Integration with the existing availability and task-management modules should be verified before claiming that all operations pass through those modules.

## System Workflow

1. A student registers or logs in.
2. Flask verifies the submitted credentials.
3. The student accesses the dashboard.
4. The student records laboratory sessions in the timetable.
5. The availability logic can process the schedule to identify qualifying free intervals.
6. A student creates a parcel pickup task.
7. Other students can view open tasks and submit pickup requests.
8. Task requests and assignments are stored in the database.
9. Students can view their activities and update their profiles.

## Scheduling and Availability Rules

CampusHelp uses the following scheduling assumptions:

| Rule | Description |
|---|---|
| Pickup window | 8:00 AM–1:00 PM |
| Pickup duration | 15 continuous minutes |
| Lab duration | 100 minutes, according to the project requirement |
| Short gaps | Gaps of 10 minutes or less between consecutive labs are treated as busy |
| Sunday | No scheduled classes under the project's assumptions |

### Example

Suppose a student has a laboratory session from 9:50 AM to 11:30 AM.

| Time interval | Classification |
|---|---|
| 8:00–9:50 AM | Free |
| 9:50–11:30 AM | Laboratory session |
| 11:30 AM–1:00 PM | Free |

Both free intervals are at least 15 minutes long, so the student has potential availability for a pickup on that day.

The calculation should consider all free intervals within the pickup window, rather than requiring the student to be free for the entire window.

## Database Design

The CampusHelp database uses MySQL to organize application data into related tables.

### 1. Students

Stores student account and profile information.

Typical attributes:
- `reg_no` — Primary key
- `name`
- `email`
- `password_hash`
- `department`
- `semester`
- `phone`
- `created_at`

### 2. Timetables

Stores timetable records associated with students.

Typical attributes:
- `timetable_id` — Primary key
- `reg_no` — Foreign key referencing students
- `image_path`
- `uploaded_at`
- `status`

### 3. Classes

Stores individual laboratory sessions.

Typical attributes:
- `class_id` — Primary key
- `timetable_id` — Foreign key referencing timetables
- `day_of_week`
- `start_time`
- `end_time`
- `subject`

### 4. Tasks

Stores parcel pickup task details.

Typical attributes:
- `task_id` — Primary key
- `created_by` — Foreign key referencing students
- `title`
- `description`
- `location`
- `task_date`
- `start_time`
- `end_time`
- `status`
- `created_at`

### 5. Task Requests

Stores student requests associated with pickup tasks.

Typical attributes:
- `request_id` — Primary key
- `task_id` — Foreign key referencing tasks
- `reg_no` — Foreign key referencing students
- `requested_at`
- `status`

### 6. Assignments

Stores assignment information for pickup tasks.

Typical attributes:
- `assignment_id` — Primary key
- `task_id` — Foreign key referencing tasks
- `reg_no` — Foreign key referencing students
- `assigned_at`
- `completed_at`
- `status`

### 7. Availability

Stores availability records associated with students, when used by the application.

Typical attributes:
- `availability_id` — Primary key
- `reg_no` — Foreign key referencing students
- `available_date`
- `start_time`
- `end_time`
- `is_available`
- `source`

*The attributes above summarize the intended schema. Verify them against the actual `SHOW CREATE TABLE` output before treating this list as the exact database definition.*

## Database Normalization

The database separates student, timetable, class, task, request, assignment, and availability information into distinct tables.

### First Normal Form (1NF)
Fields contain individual values, and repeated laboratory sessions are represented as separate records in the `classes` table.

### Second Normal Form (2NF)
The tables primarily use single-column primary keys, so partial dependency on only part of a composite primary key does not apply to those primary keys.

### Third Normal Form (3NF)
Different entities are stored in separate tables, with foreign keys connecting related records. This reduces unnecessary duplication and improves consistency.

Formal confirmation of 3NF requires checking candidate keys and functional dependencies for the actual schema.

## User Interface

The Flask web application provides a browser-based interface with a consistent, campus-focused design using green accents, light backgrounds, rounded cards, and clearly labelled forms.

### Landing Page
Introduces CampusHelp and provides navigation to registration and login.

### Login and Registration
Allows students to create accounts and sign in using their registration number or email address and password.

### Dashboard
Provides a personalized welcome, access to open pickup tasks, an overview of assignments, and navigation to the main features.

### Timetable Management
Displays saved laboratory sessions and provides a form for entering a day, subject, start time, and end time.

### Parcel Tasks
Allows students to post pickup requests, view open tasks, submit requests to help, and view their own tasks and requests.

### Student Profile
Allows students to update their name, email, department, semester, and phone number.

### Frontend and Backend Integration

The browser sends requests to Flask. Flask processes the submitted information and executes database queries through MySQL Connector/Python. The resulting data is used to render pages and display feedback to the student.

## Project Structure

The project contains the original Python backend and the Flask web interface.

```text
CampusHelp/
├── app.py
├── main.py
├── database.py
├── timetable.py
├── availability.py
├── tasks.py
├── templates/
│   └── page.html
├── static/
│   ├── style.css
│   └── app.js
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The files `templates/page.html` and `static/` contain the web interface. `app.py` contains Flask routes. The existing Python modules contain the original CLI and application logic.

The `schema.sql` file is included if it exists in the repository. Database scripts should be checked against the current schema before being executed.

## Installation and Setup

### Prerequisites

- Python installed on Windows.
- MySQL Server running.
- Visual Studio Code.
- Git, if cloning the repository.

### 1. Clone the repository

```powershell
git clone https://github.com/vaii7x/CampusHelp.git
cd CampusHelp
```

If the repository is already on your computer, open the existing folder instead.

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If the dependency list is incomplete, install the required packages:

```powershell
python -m pip install Flask mysql-connector-python python-dotenv
```

### 4. Configure environment variables

Create a local `.env` file in the same directory as `app.py`, using `.env.example` as a template.

Example:

```dotenv
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=CampusHelp
FLASK_SECRET_KEY=your_generated_secret_key
```

Replace the example values with your own local settings. If your MySQL account uses no password, leave `DB_PASSWORD=` empty.

**Never commit `.env` or real credentials to GitHub.**

### 5. Prepare the database

Make sure the `CampusHelp` database and required tables exist. If using `schema.sql` to create a fresh database, review the script first. Do not rerun a schema script against an existing database without understanding its effects.

### 6. Run the application

```powershell
python app.py
```

Open the following address in a browser:

```text
http://127.0.0.1:5000
```

## Testing

The following test cases can be used to evaluate the application.

| Test case | Expected result |
|---|---|
| Register a new student | Student record is created |
| Sign in with valid credentials | Dashboard is displayed |
| Sign in with invalid credentials | Login is rejected |
| Add a laboratory session | Session appears in the timetable |
| Create a pickup task | Task appears in the task list |
| Submit a pickup request | Request is recorded |
| Update profile information | Updated information is displayed |
| Access a protected page while logged out | Student is redirected to login |
| Calculate availability around a lab | Free intervals follow the scheduling rules |

Record actual outcomes as Pass, Fail, or Not Tested. Only mark cases as passed after testing them.

## Limitations

- Availability depends on the correctness of the laboratory schedule entered by students.
- The current interface and original CLI backend may require further integration.
- The website's current routes do not necessarily use every existing backend function.
- Automated timetable-image extraction should not be considered implemented unless it has been developed and tested.
- Additional security hardening is needed before public deployment.

## Future Enhancements

- Automated timetable extraction using OCR.
- Notifications for new requests and assignment updates.
- Improved matching of students to pickup tasks based on schedule and location.
- Administrative tools for monitoring tasks.
- Enhanced mobile usability.
- Password reset and account recovery.
- Audit logging and stronger access controls.
- Integration of the Flask interface with the existing availability and assignment logic.

## Conclusion

CampusHelp provides a structured approach to parcel pickup coordination within a university campus. By combining Python, Flask, HTML, CSS, JavaScript, and MySQL, the project brings student information, laboratory schedules, and parcel task management into a single application.

The system demonstrates the use of relational database design, web development, authentication, and scheduling logic in a practical campus scenario. Further integration, testing, and security improvements can strengthen the application and prepare it for broader use.

## Repository

Source code and documentation: https://github.com/vaii7x/CampusHelp
