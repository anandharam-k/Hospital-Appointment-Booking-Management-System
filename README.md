# MedSchedule - Hospital Appointment Booking Management System

> **Eliminating Hospital Appointment Delays Through Real-Time Outpatient Scheduling**

A production-grade, full-stack Hospital Appointment Booking Management System developed strictly for **outpatient appointment scheduling and clinical queue management**. Designed with pure **HTML5 and CSS3** on the frontend, and dual enterprise backend implementations in **Python** and **Java (Spring Boot)** backed by a relational database schema.

---

## 1. Problem Solved: "Hospital Appointment Delays"

Traditional hospital outpatient departments (OPD) suffer from severe patient delays, overcrowded waiting rooms, and administrative double-booking errors. **MedSchedule** solves this by:

1. **Instant Slot Verification**: Patients see live 30-minute doctor consultation windows.
2. **Atomic Double-Booking Prevention**: A unique database constraint (`doctor_id`, `appointment_date`, `appointment_time`) strictly blocks duplicate reservations.
3. **Queue-Free OPD Passes**: Generates a standardized Appointment ID (`APT-YYYYMMDD-XXX`) with assigned consultation room numbers.
4. **Real-Time Schedule Management**: Hospital administration can configure morning/evening shifts and manage patient statuses (Confirm, Cancel, Reschedule, Complete).

---

## 2. Technology Stack

### Frontend
- **HTML5**: Semantic, accessible markup for all 13 hospital pages.
- **CSS3**: Pure custom stylesheet (`style.css` and `responsive.css`).
- **Zero Frameworks**: No React, Angular, Vue, Bootstrap, or Tailwind CSS.
- **Responsive**: Fully optimized for Desktop, Laptop, Tablet, and Mobile devices.

### Backend Implementations
- **Python**:
  - `backend/python/app.py`: High-performance, zero-dependency REST API server using the Python Standard Library (`http.server`, `sqlite3`, `hashlib`, `json`).
  - Auto-initializes SQLite database from `schema.sql`.
- **Java (Spring Boot)**:
  - `backend/java/`: Full Spring Boot 3 + Spring Data JPA + Hibernate backend.
  - REST controllers, service layer, transactional duplicate checking, and Maven `pom.xml`.

### Database
- **Relational SQL**: `database/schema.sql` (compatible with SQLite, MySQL, and PostgreSQL).

---

## 3. Project Directory Structure

```text
/
├── frontend/                     # Pure HTML5 & CSS3 Interface
│   ├── index.html                # Professional Hospital Landing Page
│   ├── login.html                # Patient Account Login
│   ├── register.html             # Patient Registration Page
│   ├── doctors.html              # Doctor Search with Department Filters
│   ├── booking.html              # 5-Step Appointment Booking Wizard
│   ├── confirmation.html         # Booking Confirmation & OPD Pass Slip
│   ├── appointments.html         # My Upcoming Appointments & Reschedule Modal
│   ├── history.html              # Chronological Past Appointment Records
│   ├── admin-login.html          # Hospital Staff & Management Login
│   ├── admin-dashboard.html      # Hospital Management Operational Dashboard
│   ├── admin-appointments.html   # Master Appointment Management Register
│   ├── doctors-management.html   # Doctor CRUD & Consultation Room Assign
│   ├── availability.html         # Shift Scheduler & Real-Time Slot Generator
│   ├── css/
│   │   ├── style.css             # Medical Design System (Zero Frameworks)
│   │   └── responsive.css        # Multi-Device Media Queries
│   └── js/
│       └── api.js                # Unified REST API & Local Synchronization Layer
├── backend/
│   ├── python/                   # Python REST Backend
│   │   ├── app.py                # Standalone Python HTTP & SQLite Server
│   │   └── requirements.txt      # Optional dependencies
│   └── java/                     # Java Spring Boot Enterprise Backend
│       ├── pom.xml               # Maven Project Configuration
│       └── src/main/java/com/hospital/booking/
│           ├── HospitalBookingApplication.java
│           ├── model/            # JPA Entities (Appointment, Doctor, User, etc.)
│           ├── repository/       # Spring Data Repositories
│           ├── service/          # Business Logic & Double-Booking Checks
│           └── controller/       # REST Endpoints (/api/appointments, etc.)
├── database/
│   └── schema.sql                # Complete Relational Database Schema & Seeds
└── README.md
```

---

## 4. Quick Start & Execution

### Option A: Running the Frontend (AI Studio / Dev Server)
The development server serves on port 3000:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser. All pages are connected through proper navigation.

### Option B: Running the Python Backend
No external packages needed! Runs with Python 3 Standard Library:
```bash
python3 backend/python/app.py 5000
```
- Listens on `http://127.0.0.1:5000`
- Automatically initializes `hospital_booking.db` using `database/schema.sql` on first run.

### Option C: Running the Java Spring Boot Backend
Navigate to the Java directory:
```bash
cd backend/java
mvn spring-boot:run
```
- Runs on port 8080 with embedded in-memory database and H2 console at `/h2-console`.

---

## 5. Demo Credentials

### Patient Portal
- **Email**: `john.miller@example.com`
- **Password**: `patient123`
*(Or click the "Auto-Fill Demo Credentials" button on `login.html`)*

### Hospital Management / Staff Portal
- **Staff Email**: `admin@metrohealth.org`
- **Password**: `admin123`
*(Or click the "Auto-Fill Staff Credentials" button on `admin-login.html`)*

---

## 6. Relational Database Schema

### `hospitals`
- `hospital_id` (PK)
- `hospital_name`, `address`, `phone`, `email`

### `users`
- `user_id` (PK)
- `full_name`, `email` (UNIQUE), `mobile`, `password_hash`, `date_of_birth`, `gender`, `role` (`patient`, `admin`, `staff`)

### `doctors`
- `doctor_id` (PK)
- `hospital_id` (FK)
- `doctor_name`, `specialization`, `department`, `experience_years`, `available_days`, `room_number`, `status`

### `doctor_availability`
- `availability_id` (PK)
- `doctor_id` (FK)
- `shift_date`, `start_time`, `end_time`, `slot_duration_minutes` (Default: 30)

### `appointments`
- `appointment_id` (PK, formatted: `APT-YYYYMMDD-XXX`)
- `user_id` (FK), `doctor_id` (FK), `hospital_id` (FK)
- `patient_name`, `patient_mobile`, `appointment_date`, `appointment_time`
- `status` (`Confirmed`, `Pending`, `Cancelled`, `Completed`, `Rescheduled`)
- `consultation_reason`, `created_at`, `updated_at`
- **`CONSTRAINT unique_doctor_slot UNIQUE (doctor_id, appointment_date, appointment_time)`**

---

## 7. Core Workflows

### Patient Consultation Booking
1. Register or Log in to the Patient Portal.
2. Search doctors by Medical Department (Cardiology, Orthopedics, Neurology, Pediatrics, General Medicine, Oncology).
3. Select an appointment date.
4. View live 30-minute time slots (booked slots are disabled).
5. Enter patient name, mobile, and consultation reason.
6. Confirm booking to receive the instant Appointment Pass (e.g., `APT-20260929-001`).
7. Manage, reschedule, or cancel visits from "My Appointments".

### Hospital Administration
1. Log in securely via the Staff Portal (`admin-login.html`).
2. Monitor real-time statistics: Today's Appointments, Pending, Confirmed, Completed, Cancelled.
3. Update consultation status on today's schedule table.
4. Filter all hospital records by doctor, date, patient, or status.
5. Add and manage hospital medical faculty and consultation room assignments.
6. Configure doctor availability shifts (e.g. 09:00 AM – 01:00 PM, 04:00 PM – 07:00 PM) to generate slots automatically.
