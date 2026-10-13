# Smart & Secure AI-Based Examination Management & Proctoring System

An enterprise-grade, end-to-end web application built using **Flask, MySQL, HTML5, CSS3, JavaScript, and Bootstrap 5** for modern educational institutions. The system digitizes examination operations, automated seat allocation, real-time identity verification, attendance logging, incident management, and simulated AI proctoring surveillance.

---

## 1. Problem Statement

Traditional university examination management suffers from fragmented workflows:
- **Manual Seat Allocation:** Susceptible to human error, double-booking, and inefficient room utilization.
- **Attendance Bottlenecks:** Paper rosters delay student verification and impede real-time absent/late tracking.
- **Malpractice Vulnerabilities:** Difficult for individual invigilators in large halls to detect unauthorized devices, multiple faces, or abnormal movements.
- **Decentralized Records:** Hall tickets, seating allocations, incident reports, and post-exam statistics remain disconnected across administrative offices.

---

## 2. Project Objectives

1. **Automate Seating Allocation:** Implement a deterministic, collision-free allocation algorithm across designated halls without capacity overflow.
2. **Streamline Role-Based Workflows:** Deliver dedicated portals for Administrators, Invigilators, and Students.
3. **Simulate Intelligent Proctoring:** Provide a modular heuristic AI proctoring engine that flags suspicious activities (e.g., cell phone usage, face absence/duplication, suspicious movement).
4. **Digitize Real-Time Attendance:** Enable instant invigilator roll-call, hall ticket barcode/registration verification, and incident documentation.
5. **Ensure Robust Accessibility & UI/UX:** Built with light/dark theme switching, responsive layouts, print-ready hall tickets, keyboard accessibility, and site search.

---

## 3. Key Features

- **Role-Based Access Control (RBAC):** Distinct dashboards and route decorators for `ADMIN`, `INVIGILATOR`, and `STUDENT`.
- **Smart Seat Allocation:** Room capacity validation, sequential/randomized seat mapping, and conflict prevention.
- **Automated Hall Ticket Generation:** Clean, print-ready digital hall tickets with student metadata and exam timetables.
- **Real-Time Attendance Marking:** Fast single-click attendance logging (`Present`, `Absent`, `Late`) with verification badges.
- **AI Proctoring Simulator:** Real-time heuristic anomaly detection generating timestamped alerts with severity levels and confidence scores.
- **Incident Management:** Incident reporting with invigilator logs, severity tags, and administrative resolution workflows.
- **Comprehensive Analytics & Reports:** Interactive Chart.js visual summaries, attendance distribution charts, and printable administrative rosters.
- **Modern UI/UX Features:**
  - Dark/Light mode toggle with persistence
  - Accessible global search (`Ctrl+K` / `Cmd+K`)
  - Skip-to-content accessibility link (`WCAG 2.1`)
  - Non-intrusive cookie consent banner
  - Responsive mobile drawer navigation
  - Password visibility toggle on authentication forms
  - One-click copy-to-clipboard for registration numbers and exam IDs
  - Reusable confirmation dialogs for destructive actions
  - Expandable Help & FAQ portal with real-time keyword filtering

---

## 4. Technology Stack

- **Backend:** Python 3.9+, Flask, Flask-Session, Werkzeug
- **Database:** MySQL 8.0+, `mysql-connector-python`
- **Frontend:** HTML5, CSS3 Custom Properties (Tokens), Vanilla JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4
- **Testing:** Pytest, Unittest

---

## 5. System Architecture

The application implements a clean three-tier architectural pattern:

```
┌────────────────────────────────────────────────────────┐
│             Presentation Layer (Frontend)              │
│    HTML5 (Jinja2) · CSS3 Tokens · JS (ES6) · Bootstrap 5 │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP / REST / JSON
┌───────────────────────────▼────────────────────────────┐
│              Application Layer (Flask Backend)         │
│  Blueprints · Auth & RBAC · Services · Heuristic Engine│
└───────────────────────────▲────────────────────────────┘
                            │ Parameterized SQL
┌───────────────────────────▼────────────────────────────┐
│               Data Layer (MySQL Database)              │
│   15 Relational Tables · Triggers · Views · Constraints│
└────────────────────────────────────────────────────────┘
```

For comprehensive details on services and database design, refer to [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 6. Main Database Entities and Relationships

The relational schema strictly enforces referential integrity across 15 entities:
- **`User`**: Base authentication table storing role-based credentials and password hashes.
- **`Department`**: Academic departments (`CSE`, `ECE`, `MECH`).
- **`Student`**: Enrolled students with registration numbers linked to `User` and `Department`.
- **`Invigilator`**: Faculty members with employee IDs and department associations.
- **`Subject`**: Courses offering credits, subject codes, and syllabus details.
- **`Room`**: Examination halls with seat capacity metrics.
- **`Exam`**: Scheduled examination sessions tying subject, date, time, and session.
- **`ExamRegistration`**: Student registrations for specific examinations.
- **`SeatAllocation`**: Generated mappings associating student, exam, room, and seat number.
- **`Attendance`**: Attendance logs (`PRESENT`, `ABSENT`, `LATE`) and verification timestamps.
- **`AIAlert`**: Automated proctoring heuristic warnings with confidence scores.
- **`Incident`**: Official incident reports recorded by invigilators.

---

## 7. Project Folder Structure

```
├── .env.example              # Template for environment configuration
├── .gitignore                # Git exclusions (secrets, caches, virtualenvs)
├── ARCHITECTURE.md           # Architectural documentation
├── README.md                 # Project documentation
├── UI_UX_AUDIT.md            # Audit of 20 UI/UX enhancement criteria
├── UI_UX_IMPLEMENTATION.md   # Implementation details of enhancements
├── generate_seed.py          # Script generating hash-secured seed fixtures
├── requirements.txt          # Python dependencies
├── run.py                    # Flask development server entrypoint
├── app/                      # Application package
│   ├── __init__.py           # Flask app factory, blueprint registration
│   ├── config.py             # Central environment variable configuration
│   ├── database/             # Parameterized SQL query modules
│   │   ├── __init__.py       # Database connection pool manager
│   │   ├── admin_queries.py  # Admin queries
│   │   ├── search_queries.py # Search queries
│   │   └── ...               # Additional query services
│   ├── routes/               # Flask Blueprint route handlers
│   │   ├── auth.py           # Authentication routes (login, logout)
│   │   ├── admin/            # Admin CRUD & management routes
│   │   ├── student/          # Student portal & hall ticket routes
│   │   ├── invigilator/      # Invigilator attendance & incident routes
│   │   ├── help_routes.py    # Help & FAQ routes
│   │   └── search_routes.py  # Global search API
│   ├── services/             # Business logic & simulation services
│   │   ├── auth_service.py   # Password verification & session management
│   │   ├── proctoring.py     # AI proctoring heuristic simulation
│   │   ├── seating.py        # Smart seat allocation algorithm
│   │   └── utm_service.py    # Privacy-conscious campaign attribution
│   ├── static/               # Client assets
│   │   ├── css/style.css     # CSS design system & print stylesheet
│   │   └── js/main.js        # Interactive UI controller
│   └── templates/            # Jinja2 templates (Admin, Student, Invigilator)
├── sql/                      # Relational database scripts
│   ├── schema.sql            # Schema definitions, foreign keys, triggers
│   ├── seed.sql              # Seed database records
│   └── views.sql             # Analytical database views
└── tests/                    # Automated pytest test suite
    ├── conftest.py           # Test fixtures and database cleanup
    ├── test_stage1.py        # Stage 1 foundation tests
    ├── test_stage2_admin.py  # Stage 2 admin tests
    ├── test_stage3_operations.py # Stage 3 operations tests
    ├── test_stage4_proctoring.py # Stage 4 proctoring tests
    ├── test_stage5_reports.py    # Stage 5 report tests
    └── test_ui_ux_enhancements.py# UI/UX enhancements tests
```

---

## 8. Prerequisites (macOS)

- **Operating System:** macOS Monterey (12.0) or later
- **Python:** Python 3.9+ (`python3 --version`)
- **Package Manager:** Homebrew (`brew --version`)
- **Database:** MySQL 8.0+ (`mysql --version`)

---

## 9. Installation Instructions

### Step 1: Clone the Repository
```bash
git clone https://github.com/devansh6107/smart-secure-examination-management-system.git
cd smart-secure-examination-management-system
```

### Step 2: Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 10. MySQL Database Setup

1. Start your local MySQL service (if not running):
   ```bash
   brew services start mysql
   ```
2. Log into MySQL and create the database:
   ```bash
   mysql -u root -p
   ```
   ```sql
   CREATE DATABASE IF NOT EXISTS exam_management_db;
   EXIT;
   ```
3. Run the database schema, views, and seed data:
   ```bash
   mysql -u root -p exam_management_db < sql/schema.sql
   mysql -u root -p exam_management_db < sql/views.sql
   mysql -u root -p exam_management_db < sql/seed.sql
   ```

---

## 11. Environment Variable Configuration

Create your local `.env` file from the provided `.env.example`:
```bash
cp .env.example .env
```

Configure your local credentials in `.env`:
```ini
# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=exam_management_db
DB_USER=root
DB_PASSWORD=your_actual_mysql_password

# Flask Application Configuration
SECRET_KEY=generate_a_secure_random_key_here
FLASK_DEBUG=True
FLASK_PORT=5001
```

> [!IMPORTANT]
> The `.env` file is excluded from Git to prevent exposing credentials. Never commit `.env` to source control.

---

## 12. Starting the Application

With your virtual environment active and `.env` configured:
```bash
python3 run.py
```

The application runs locally on:
**[http://localhost:5001](http://localhost:5001)**

*(Note: The server must be actively running locally in your terminal for this URL to be reachable.)*

---

## 13. Cloud & Vercel Deployment

The application supports zero-config deployment to **Vercel** serverless with cloud MySQL (e.g., **Aiven**):

### 1. Database Connection & TLS
Configure your Aiven / cloud MySQL environment variables in Vercel project settings:
```ini
DB_HOST=exam-management-db-devanshghosh6107-9509.e.aivencloud.com
DB_PORT=18298
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=<your_aiven_password>
DB_SSL_REQUIRED=True
DB_SSL_VERIFY_CERT=True
SECRET_KEY=<your_production_secret_key>
```

### 2. Vercel Configuration
- Entrypoint: [`api/index.py`](api/index.py) (exposes WSGI `app`)
- Routing: [`vercel.json`](vercel.json) routes incoming requests directly to the WSGI application
- Database migrations: Run `python3 init_database.py` once to populate schema, views, procedures, and seed data.

---

## 14. Running Automated Tests

Run the complete automated test suite using pytest:
```bash
python3 -m pytest
```

Expected output:
```
============================== 45 passed in 1.38s ==============================
```

The test suite covers:
- Core authentication, password hashing, session RBAC
- Admin student, invigilator, room, exam, and department CRUD
- Deterministic seat allocation algorithms
- AI proctoring heuristic simulator
- View exports, attendance reports, and summary generation
- UI/UX enhancement endpoints (UTM attribution, search API, FAQ, error states)

---

## 14. Demo Accounts

The database seed script (`sql/seed.sql`) populates pre-configured test users:

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Full access to exams, rooms, students, reports |
| **Invigilator** | `dr.sharma` | `invig123` | Assigned hall attendance & incident reporting |
| **Student** | `REG001` *(or `rahul.kumar`)* | `student123` | View exam schedules & digital hall ticket |

---

## 15. AI Simulation Limitations

- **Heuristic Emulation:** The proctoring system currently runs in **simulation mode** via `app/services/proctoring.py`. It simulates confidence intervals and detection events using probabilistic heuristics.
- **Pluggable Architecture:** The proctoring interface is designed as an abstraction layer. It can be connected to real-time computer vision models (e.g., OpenCV, YOLOv8, MediaPipe) without restructuring database schemas or API routes.

---

## 16. Future Scope

- **Real-Time Video Streaming:** WebRTC integration for continuous webcam monitoring.
- **Facial Recognition:** Automated face-matching against institutional student database records.
- **PDF Generation:** Server-side PDF generation for formal administrative hall ticket archiving.
- **Multi-Factor Authentication (MFA):** TOTP authentication for administrative accounts.
