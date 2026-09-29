-- =====================================================================
-- Hospital Appointment Booking Management System - Relational Schema
-- Target: SQLite / MySQL / PostgreSQL Compatible
-- Purpose: Eradicate Hospital Appointment Delays through Real-Time Scheduling
-- =====================================================================

-- 1. HOSPITALS TABLE
CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name VARCHAR(150) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. USERS TABLE (Patients and Hospital Management Staff)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    mobile VARCHAR(25) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(15) NOT NULL, -- Male, Female, Other
    role VARCHAR(20) NOT NULL DEFAULT 'patient', -- 'patient', 'admin', 'staff'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. DOCTORS TABLE
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL DEFAULT 1,
    doctor_name VARCHAR(120) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    experience_years INTEGER NOT NULL,
    available_days VARCHAR(100) NOT NULL, -- e.g. "Mon, Tue, Wed, Thu, Fri"
    room_number VARCHAR(30) NOT NULL DEFAULT 'OPD-101',
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'on_leave', 'inactive'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id) ON DELETE CASCADE
);

-- 4. DOCTOR AVAILABILITY TABLE (Working shifts for slot generation)
CREATE TABLE IF NOT EXISTS doctor_availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL,
    shift_date DATE NOT NULL,
    start_time VARCHAR(10) NOT NULL, -- e.g. "09:00"
    end_time VARCHAR(10) NOT NULL,   -- e.g. "13:00"
    slot_duration_minutes INTEGER NOT NULL DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- 5. APPOINTMENTS TABLE
-- Crucial: Prevents duplicate bookings via UNIQUE constraint on (doctor_id, appointment_date, appointment_time)
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(30) PRIMARY KEY, -- Formatted: APT-YYYYMMDD-XXX
    user_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    hospital_id INTEGER NOT NULL DEFAULT 1,
    patient_name VARCHAR(120) NOT NULL,
    patient_mobile VARCHAR(25) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(15) NOT NULL, -- e.g. "09:30 AM"
    status VARCHAR(25) NOT NULL DEFAULT 'Confirmed', -- 'Confirmed', 'Pending', 'Cancelled', 'Completed', 'Rescheduled'
    consultation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    CONSTRAINT unique_doctor_slot UNIQUE (doctor_id, appointment_date, appointment_time)
);

-- INDEXES FOR FAST QUERYING AND APPOINTMENT LOOKUPS
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments (doctor_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_user ON appointments (user_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments (status);
CREATE INDEX IF NOT EXISTS idx_doctors_dept ON doctors (department);
CREATE INDEX IF NOT EXISTS idx_availability_doc_date ON doctor_availability (doctor_id, shift_date);

-- =====================================================================
-- INITIAL SEED DATA
-- =====================================================================

-- Seed Hospital
INSERT OR IGNORE INTO hospitals (hospital_id, hospital_name, address, phone, email) 
VALUES (1, 'ApexCare Central Hospital', '450 Healthcare Boulevard, Medical District, Suite 100', '+1 (800) 555-0199', 'appointments@apexcarehealth.org');

-- Seed Admin Staff (Password: admin123, SHA-256 hashed)
-- Password 'admin123' sha256 is: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
INSERT OR IGNORE INTO users (user_id, full_name, email, mobile, password_hash, date_of_birth, gender, role)
VALUES (1, 'Dr. Sarah Mitchell (Staff Admin)', 'admin@metrohealth.org', '+1 (555) 012-3456', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '1982-04-15', 'Female', 'admin');

-- Seed Sample Patient (Password: patient123)
-- Password 'patient123' sha256 is: ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
INSERT OR IGNORE INTO users (user_id, full_name, email, mobile, password_hash, date_of_birth, gender, role)
VALUES (2, 'Johnathan Miller', 'john.miller@example.com', '+1 (555) 987-6543', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', '1990-08-22', 'Male', 'patient');

INSERT OR IGNORE INTO users (user_id, full_name, email, mobile, password_hash, date_of_birth, gender, role)
VALUES (3, 'Eleanor Vance', 'eleanor.v@example.com', '+1 (555) 432-8765', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', '1985-11-10', 'Female', 'patient');

-- Seed Doctors across departments
INSERT OR IGNORE INTO doctors (doctor_id, hospital_id, doctor_name, specialization, department, experience_years, available_days, room_number, status)
VALUES 
(1, 1, 'Dr. Arun Kumar', 'Senior Cardiologist & Interventional Specialist', 'Cardiology', 16, 'Mon, Tue, Wed, Thu, Fri', 'OPD-102', 'active'),
(2, 1, 'Dr. Priya Sharma', 'Consultant Orthopedic Surgeon', 'Orthopedics', 12, 'Mon, Wed, Fri, Sat', 'OPD-105', 'active'),
(3, 1, 'Dr. Marcus Vance', 'Senior Neurologist & Stroke Consultant', 'Neurology', 18, 'Tue, Thu, Fri', 'OPD-201', 'active'),
(4, 1, 'Dr. Claire Bennett', 'Chief Pediatric Specialist', 'Pediatrics', 10, 'Mon, Tue, Wed, Thu, Fri, Sat', 'OPD-108', 'active'),
(5, 1, 'Dr. David Chen', 'Consultant Physician & Diabetologist', 'General Medicine', 14, 'Mon, Tue, Wed, Thu, Fri', 'OPD-104', 'active'),
(6, 1, 'Dr. Anita Roy', 'Senior Clinical Oncologist', 'Oncology', 15, 'Mon, Wed, Fri', 'OPD-210', 'active');

-- Seed Doctor Availability Schedules (Today & Upcoming Days)
INSERT OR IGNORE INTO doctor_availability (availability_id, doctor_id, shift_date, start_time, end_time, slot_duration_minutes)
VALUES
(1, 1, '2026-09-29', '09:00', '13:00', 30),
(2, 1, '2026-09-29', '16:00', '19:00', 30),
(3, 1, '2026-09-30', '09:00', '13:00', 30),
(4, 2, '2026-09-29', '09:30', '13:30', 30),
(5, 2, '2026-09-30', '14:00', '18:00', 30),
(6, 3, '2026-09-29', '10:00', '14:00', 30),
(7, 4, '2026-09-29', '09:00', '13:00', 30),
(8, 5, '2026-09-29', '08:30', '12:30', 30),
(9, 6, '2026-09-29', '11:00', '15:00', 30);

-- Seed Sample Appointments
INSERT OR IGNORE INTO appointments (appointment_id, user_id, doctor_id, hospital_id, patient_name, patient_mobile, appointment_date, appointment_time, status, consultation_reason)
VALUES
('APT-20260929-001', 2, 1, 1, 'Johnathan Miller', '+1 (555) 987-6543', '2026-09-29', '09:30 AM', 'Confirmed', 'Routine cardiovascular follow-up check'),
('APT-20260929-002', 3, 2, 1, 'Eleanor Vance', '+1 (555) 432-8765', '2026-09-29', '10:00 AM', 'Confirmed', 'Knee joint discomfort and movement assessment'),
('APT-20260929-003', 2, 4, 1, 'Baby Leo Miller', '+1 (555) 987-6543', '2026-09-29', '11:00 AM', 'Pending', 'Scheduled childhood vaccination and wellness check'),
('APT-20260928-094', 2, 5, 1, 'Johnathan Miller', '+1 (555) 987-6543', '2026-09-28', '09:00 AM', 'Completed', 'Annual executive blood glucose review'),
('APT-20260925-081', 3, 1, 1, 'Eleanor Vance', '+1 (555) 432-8765', '2026-09-25', '04:30 PM', 'Cancelled', 'Patient requested cancellation due to travel');
