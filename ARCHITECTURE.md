# Architecture Document

## System Overview
The Smart & Secure AI-Based Examination Management System is a modular monolith built in Python using the Flask framework. It provides distinct portals for Admins, Invigilators, and Students, connected to a robust, normalized MySQL 8+ database.

## 1. Design Patterns
- **Model-View-Controller (MVC)**: 
  - **Model**: Abstracted through raw SQL queries in `app/database/` interacting directly with MySQL.
  - **View**: Jinja2 HTML templates in `app/templates/`.
  - **Controller**: Flask Blueprints acting as route handlers in `app/routes/`.
- **Service Object Pattern**: Complex domain logic (e.g., AI simulation, smart seating) is abstracted into service objects (`app/services/proctoring_service.py`) to keep route controllers thin and make swapping the simulator for real ML logic seamless.

## 2. Directory Structure
```text
.
├── app/
│   ├── __init__.py           # App factory, DB config, Blueprint registration
│   ├── database/             # Data Access Layer
│   │   ├── admin_queries.py  # Admin-specific SQL functions
│   │   ├── operational_queries.py # Invigilator/Exam operational SQL
│   ├── routes/               # Controllers (Blueprints)
│   │   ├── admin_routes.py   # Main admin routes and auth checks
│   │   ├── admin/            # Sub-module blueprints (alerts, reports, etc.)
│   │   ├── invigilator_routes.py
│   │   └── student_routes.py
│   ├── services/             # Business Logic
│   │   └── proctoring_service.py # AI Simulator Logic
│   └── templates/            # Presentation Layer
│       ├── base.html         # Base layout
│       ├── admin/
│       ├── invigilator/
│       └── student/
├── sql/
│   ├── schema.sql            # Table definitions, Views, Triggers, Procs
│   ├── seed.sql              # Deterministic test data
│   └── queries.sql           # Representative academic DBMS queries
├── tests/                    # Automated testing suite
├── README.md
├── ARCHITECTURE.md
├── requirements.txt
└── run.py                    # Application entrypoint
```

## 3. Database Architecture
The database (`exam_management_db`) uses 15 normalized tables (InnoDB) ensuring data integrity.

### Key Workflows:
1. **Authentication**: `User` table (1-to-1 mapped with `Student` and `Invigilator`).
2. **Setup**: `Department`, `Subject`, `ExamRoom`, and `Seat` define the physical and academic constraints.
3. **Execution**: `Exam` binds a subject, room, and invigilator together. `ExamRegistration` maps students to exams (many-to-many).
4. **Operations**: `SeatAllocation` maps a student to a specific seat for an exam. `Attendance` and `Authentication` map 1-to-1 with allocations.
5. **Monitoring**: `AIAlert` and `Incident` records tie directly back to an individual `SeatAllocation`.

### Advanced DBMS Features Implemented
- **Views**: `vw_exam_summary` encapsulates complex JOINs and aggregations.
- **Stored Procedures & Transactions**: `sp_reallocate_student` safely updates seat allocations.
- **Triggers**: `trg_after_incident_insert` audits high-risk incidents.

## 4. Security
- **Authentication**: `werkzeug.security` is used to hash passwords (`pbkdf2:sha256`).
- **Authorization**: Custom decorators (`@admin_required`, `@invigilator_required`) validate session roles before executing route logic.
- **SQL Injection Prevention**: All `mysql-connector-python` queries use parameterized inputs (`%s`), strictly avoiding string interpolation.

## 5. Extensibility (Stage 5+)
The system is built to replace the `ProctoringService` simulator with a live Video Analytics pipeline (OpenCV/YOLO). The frontend logic, database schema, and controllers will require zero modification, demonstrating high cohesion and low coupling.
