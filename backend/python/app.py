#!/usr/bin/env python3
"""
Hospital Appointment Booking Management System - Python Backend
Uses Python Standard Library (zero external dependencies required)
Features:
- SQLite relational persistence with transaction safety
- Atomic double-booking prevention with UNIQUE constraints
- Patient & Hospital Staff Authentication (SHA-256 password hashing)
- Real-time Slot Availability Calculation
- Full CRUD for Appointments, Doctors, and Schedules
"""

import sys
import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Resolve database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
DB_PATH = os.path.join(BASE_DIR, 'hospital_booking.db')
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'database', 'schema.sql')

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with project salt"""
    return hashlib.sha256(password.strip().encode('utf-8')).hexdigest()

def get_db():
    """Returns sqlite3 connection with Row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes schema and seed data if tables do not exist"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
    table_exists = cursor.fetchone()
    if not table_exists:
        print(f"[*] Initializing database from {SCHEMA_PATH}...")
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                cursor.executescript(schema_sql)
                conn.commit()
                print("[+] Database initialized with tables and seed data successfully.")
        else:
            print(f"[!] Warning: Schema file not found at {SCHEMA_PATH}")
    conn.close()

def generate_appointment_id(cursor, date_str: str) -> str:
    """Generates unique appointment ID formatted as APT-YYYYMMDD-XXX"""
    clean_date = date_str.replace('-', '')
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM appointments WHERE appointment_id LIKE ?",
        (f"APT-{clean_date}-%",)
    )
    count = cursor.fetchone()['cnt'] + 1
    return f"APT-{clean_date}-{count:03d}"

def calculate_time_slots(start_time_str: str, end_time_str: str, slot_duration: int = 30):
    """Generates formatted 12-hour time slots from start and end 24-hr times"""
    slots = []
    try:
        t_curr = datetime.strptime(start_time_str.strip(), "%H:%M")
        t_end = datetime.strptime(end_time_str.strip(), "%H:%M")
        while t_curr + timedelta(minutes=slot_duration) <= t_end:
            slots.append(t_curr.strftime("%I:%M %p"))
            t_curr += timedelta(minutes=slot_duration)
    except Exception as e:
        print(f"[!] Slot calculation error: {e}")
    return slots

class HospitalRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Hospital Management REST Endpoints"""

    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(body)
        except Exception:
            return {}

    def _send_json(self, data, status_code=200):
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def _send_error(self, message: str, status_code=400):
        self._send_json({"success": False, "error": message}, status_code=status_code)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        query = parse_qs(parsed.query)

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Health check
            if path == '/api' or path == '/api/health':
                self._send_json({"status": "healthy", "service": "Hospital Appointment Booking System", "version": "1.0.0"})
                return

            # Doctors List
            if path == '/api/doctors':
                dept = query.get('department', [None])[0]
                status = query.get('status', ['active'])[0]
                sql = "SELECT * FROM doctors WHERE 1=1"
                params = []
                if status and status != 'all':
                    sql += " AND status = ?"
                    params.append(status)
                if dept:
                    sql += " AND department = ?"
                    params.append(dept)
                sql += " ORDER BY doctor_name ASC"
                cursor.execute(sql, params)
                doctors = [dict(row) for row in cursor.fetchall()]
                self._send_json({"success": True, "doctors": doctors, "total": len(doctors)})
                return

            # Doctor Availability & Computed Slots
            if path == '/api/availability':
                doctor_id = query.get('doctor_id', [None])[0]
                date_str = query.get('date', [None])[0]

                if not doctor_id:
                    self._send_error("doctor_id is required")
                    return

                # Get configured shifts
                if date_str:
                    cursor.execute(
                        "SELECT * FROM doctor_availability WHERE doctor_id = ? AND shift_date = ? ORDER BY start_time ASC",
                        (doctor_id, date_str)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM doctor_availability WHERE doctor_id = ? ORDER BY shift_date ASC, start_time ASC",
                        (doctor_id,)
                    )
                shifts = [dict(r) for r in cursor.fetchall()]

                # If date is specified, calculate discrete slots and mark booked ones
                slots_info = []
                if date_str:
                    # Query all currently booked appointments for this doctor and date (exclude Cancelled)
                    cursor.execute(
                        "SELECT appointment_time FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND status != 'Cancelled'",
                        (doctor_id, date_str)
                    )
                    booked_times = {row['appointment_time'] for row in cursor.fetchall()}

                    # Generate slots from shifts, or provide default standard OPD slots (09:00 - 13:00, 16:00 - 19:00)
                    all_slots = []
                    if shifts:
                        for shift in shifts:
                            all_slots.extend(calculate_time_slots(shift['start_time'], shift['end_time'], shift['slot_duration_minutes']))
                    else:
                        # Default hospital OPD schedule
                        all_slots = [
                            "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", 
                            "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM",
                            "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM"
                        ]

                    for slot_time in all_slots:
                        slots_info.append({
                            "time": slot_time,
                            "available": slot_time not in booked_times,
                            "is_booked": slot_time in booked_times
                        })

                self._send_json({"success": True, "shifts": shifts, "slots": slots_info, "date": date_str})
                return

            # Appointments List with Multi-Criteria Filter
            if path == '/api/appointments':
                user_id = query.get('user_id', [None])[0]
                doctor_id = query.get('doctor_id', [None])[0]
                date_filter = query.get('date', [None])[0]
                status_filter = query.get('status', [None])[0]
                search = query.get('search', [None])[0]

                sql = """
                    SELECT a.*, d.doctor_name, d.specialization, d.department, d.room_number, h.hospital_name
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    JOIN hospitals h ON a.hospital_id = h.hospital_id
                    WHERE 1=1
                """
                params = []
                if user_id:
                    sql += " AND a.user_id = ?"
                    params.append(user_id)
                if doctor_id:
                    sql += " AND a.doctor_id = ?"
                    params.append(doctor_id)
                if date_filter:
                    sql += " AND a.appointment_date = ?"
                    params.append(date_filter)
                if status_filter and status_filter.lower() != 'all':
                    sql += " AND a.status = ?"
                    params.append(status_filter)
                if search:
                    sql += " AND (a.patient_name LIKE ? OR a.appointment_id LIKE ? OR a.patient_mobile LIKE ?)"
                    wildcard = f"%{search}%"
                    params.extend([wildcard, wildcard, wildcard])

                sql += " ORDER BY a.appointment_date DESC, a.appointment_time ASC"
                cursor.execute(sql, params)
                appointments = [dict(r) for r in cursor.fetchall()]
                self._send_json({"success": True, "appointments": appointments, "total": len(appointments)})
                return

            # Single Appointment Details
            if path.startswith('/api/appointments/'):
                apt_id = path.split('/')[-1]
                cursor.execute("""
                    SELECT a.*, d.doctor_name, d.specialization, d.department, d.room_number, h.hospital_name
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    JOIN hospitals h ON a.hospital_id = h.hospital_id
                    WHERE a.appointment_id = ?
                """, (apt_id,))
                apt = cursor.fetchone()
                if apt:
                    self._send_json({"success": True, "appointment": dict(apt)})
                else:
                    self._send_error("Appointment not found", 404)
                return

            # Dashboard Analytics & Statistics
            if path == '/api/dashboard/stats':
                today_str = datetime.now().strftime("%Y-%m-%d")

                # Counts by status
                cursor.execute("SELECT status, COUNT(*) as cnt FROM appointments GROUP BY status")
                status_counts = {r['status']: r['cnt'] for r in cursor.fetchall()}

                # Today's appointments count
                cursor.execute("SELECT COUNT(*) as cnt FROM appointments WHERE appointment_date = ?", (today_str,))
                today_count = cursor.fetchone()['cnt']

                # Total doctors
                cursor.execute("SELECT COUNT(*) as cnt FROM doctors WHERE status = 'active'")
                doctor_count = cursor.fetchone()['cnt']

                # Today's schedule preview
                cursor.execute("""
                    SELECT a.*, d.doctor_name, d.department, d.room_number
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    WHERE a.appointment_date = ?
                    ORDER BY a.appointment_time ASC
                """, (today_str,))
                today_schedule = [dict(r) for r in cursor.fetchall()]

                self._send_json({
                    "success": True,
                    "today_date": today_str,
                    "stats": {
                        "today": today_count,
                        "pending": status_counts.get("Pending", 0),
                        "confirmed": status_counts.get("Confirmed", 0),
                        "completed": status_counts.get("Completed", 0),
                        "cancelled": status_counts.get("Cancelled", 0),
                        "active_doctors": doctor_count
                    },
                    "today_schedule": today_schedule
                })
                return

            self._send_error("Endpoint not found", 404)

        except Exception as e:
            self._send_error(f"Internal server error: {str(e)}", 500)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        data = self._read_body()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Patient Registration
            if path == '/api/auth/register':
                required_fields = ['full_name', 'email', 'mobile', 'password', 'date_of_birth', 'gender']
                for f in required_fields:
                    if not data.get(f):
                        self._send_error(f"Missing required field: {f}")
                        return

                email = data['email'].strip().lower()
                cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    self._send_error("An account with this email address already exists.", 409)
                    return

                pwd_hash = hash_password(data['password'])
                cursor.execute("""
                    INSERT INTO users (full_name, email, mobile, password_hash, date_of_birth, gender, role)
                    VALUES (?, ?, ?, ?, ?, ?, 'patient')
                """, (data['full_name'].strip(), email, data['mobile'].strip(), pwd_hash, data['date_of_birth'], data['gender']))
                conn.commit()

                user_id = cursor.lastrowid
                self._send_json({
                    "success": True,
                    "message": "Registration successful",
                    "user": {
                        "user_id": user_id,
                        "full_name": data['full_name'],
                        "email": email,
                        "mobile": data['mobile'],
                        "role": "patient"
                    }
                }, 201)
                return

            # 2. Patient / User Login
            if path == '/api/auth/login':
                identifier = data.get('identifier', '').strip().lower()
                password = data.get('password', '')

                if not identifier or not password:
                    self._send_error("Email/Mobile and password are required")
                    return

                pwd_hash = hash_password(password)
                cursor.execute("""
                    SELECT user_id, full_name, email, mobile, date_of_birth, gender, role 
                    FROM users 
                    WHERE (LOWER(email) = ? OR mobile = ?) AND password_hash = ?
                """, (identifier, identifier, pwd_hash))
                user = cursor.fetchone()

                if not user:
                    self._send_error("Invalid email/mobile or password", 401)
                    return

                self._send_json({
                    "success": True,
                    "message": "Login successful",
                    "user": dict(user)
                })
                return

            # 3. Hospital Staff / Admin Login
            if path == '/api/auth/admin-login':
                email = data.get('email', '').strip().lower()
                password = data.get('password', '')

                if not email or not password:
                    self._send_error("Email and password are required")
                    return

                pwd_hash = hash_password(password)
                cursor.execute("""
                    SELECT user_id, full_name, email, mobile, role 
                    FROM users 
                    WHERE LOWER(email) = ? AND password_hash = ? AND role IN ('admin', 'staff')
                """, (email, pwd_hash))
                admin_user = cursor.fetchone()

                if not admin_user:
                    self._send_error("Invalid staff credentials or unauthorized access", 401)
                    return

                self._send_json({
                    "success": True,
                    "message": "Hospital staff authentication verified",
                    "user": dict(admin_user)
                })
                return

            # 4. Book Appointment (With Strict Double-Booking Prevention)
            if path == '/api/appointments':
                required_fields = ['user_id', 'doctor_id', 'patient_name', 'patient_mobile', 'appointment_date', 'appointment_time']
                for f in required_fields:
                    if not data.get(f):
                        self._send_error(f"Missing required booking field: {f}")
                        return

                doctor_id = int(data['doctor_id'])
                apt_date = data['appointment_date'].strip()
                apt_time = data['appointment_time'].strip()

                # ATOMIC CHECK: Check if the exact doctor, date, and slot is already booked and not cancelled
                cursor.execute("""
                    SELECT appointment_id, status FROM appointments
                    WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status != 'Cancelled'
                """, (doctor_id, apt_date, apt_time))
                existing = cursor.fetchone()

                if existing:
                    self._send_error(
                        f"Slot Conflict: The time slot {apt_time} on {apt_date} for this doctor is already booked. Please choose an available slot.",
                        409
                    )
                    return

                # Generate clean Appointment ID
                apt_id = generate_appointment_id(cursor, apt_date)
                hospital_id = data.get('hospital_id', 1)
                reason = data.get('consultation_reason', 'General Consultation')

                cursor.execute("""
                    INSERT INTO appointments (
                        appointment_id, user_id, doctor_id, hospital_id,
                        patient_name, patient_mobile, appointment_date,
                        appointment_time, status, consultation_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?)
                """, (
                    apt_id, int(data['user_id']), doctor_id, hospital_id,
                    data['patient_name'].strip(), data['patient_mobile'].strip(),
                    apt_date, apt_time, reason
                ))
                conn.commit()

                # Retrieve complete appointment details for receipt
                cursor.execute("""
                    SELECT a.*, d.doctor_name, d.specialization, d.department, d.room_number, h.hospital_name, h.address as hospital_address
                    FROM appointments a
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    JOIN hospitals h ON a.hospital_id = h.hospital_id
                    WHERE a.appointment_id = ?
                """, (apt_id,))
                created_apt = dict(cursor.fetchone())

                self._send_json({
                    "success": True,
                    "message": "Appointment Booked Successfully",
                    "appointment": created_apt
                }, 201)
                return

            # 5. Doctor Management: Add New Doctor
            if path == '/api/doctors':
                required_fields = ['doctor_name', 'specialization', 'department', 'experience_years', 'available_days']
                for f in required_fields:
                    if not data.get(f):
                        self._send_error(f"Missing required field: {f}")
                        return

                room = data.get('room_number', 'OPD-101')
                cursor.execute("""
                    INSERT INTO doctors (hospital_id, doctor_name, specialization, department, experience_years, available_days, room_number, status)
                    VALUES (1, ?, ?, ?, ?, ?, ?, 'active')
                """, (
                    data['doctor_name'].strip(),
                    data['specialization'].strip(),
                    data['department'].strip(),
                    int(data['experience_years']),
                    data['available_days'].strip(),
                    room
                ))
                conn.commit()
                doc_id = cursor.lastrowid
                self._send_json({"success": True, "message": "Doctor added successfully", "doctor_id": doc_id}, 201)
                return

            # 6. Availability Management: Configure Doctor Shift
            if path == '/api/availability':
                required = ['doctor_id', 'shift_date', 'start_time', 'end_time']
                for f in required:
                    if not data.get(f):
                        self._send_error(f"Missing field: {f}")
                        return

                slot_duration = int(data.get('slot_duration_minutes', 30))
                cursor.execute("""
                    INSERT INTO doctor_availability (doctor_id, shift_date, start_time, end_time, slot_duration_minutes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    int(data['doctor_id']),
                    data['shift_date'],
                    data['start_time'],
                    data['end_time'],
                    slot_duration
                ))
                conn.commit()
                avail_id = cursor.lastrowid
                self._send_json({"success": True, "message": "Doctor availability schedule configured", "availability_id": avail_id}, 201)
                return

            self._send_error("Endpoint not found", 404)

        except sqlite3.IntegrityError as ie:
            self._send_error(f"Database constraint violation: {str(ie)}", 409)
        except Exception as e:
            self._send_error(f"Server error: {str(e)}", 500)
        finally:
            conn.close()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        data = self._read_body()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Update Appointment Status or Reschedule
            # Endpoint: /api/appointments/<apt_id>/status
            if '/status' in path:
                parts = path.split('/')
                apt_id = parts[3]
                new_status = data.get('status')
                new_date = data.get('appointment_date')
                new_time = data.get('appointment_time')

                if not new_status:
                    self._send_error("New status is required")
                    return

                # If rescheduling, perform duplicate slot prevention check
                if new_status == 'Rescheduled' or (new_date and new_time):
                    # Fetch doctor ID for this appointment
                    cursor.execute("SELECT doctor_id, appointment_date, appointment_time FROM appointments WHERE appointment_id = ?", (apt_id,))
                    current_apt = cursor.fetchone()
                    if not current_apt:
                        self._send_error("Appointment not found", 404)
                        return

                    target_date = new_date or current_apt['appointment_date']
                    target_time = new_time or current_apt['appointment_time']
                    doc_id = current_apt['doctor_id']

                    # Check slot conflict with other appointments
                    cursor.execute("""
                        SELECT appointment_id FROM appointments
                        WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND appointment_id != ? AND status != 'Cancelled'
                    """, (doc_id, target_date, target_time, apt_id))
                    conflict = cursor.fetchone()

                    if conflict:
                        self._send_error(f"Slot Conflict: Doctor is already booked at {target_time} on {target_date}.", 409)
                        return

                    cursor.execute("""
                        UPDATE appointments
                        SET status = ?, appointment_date = ?, appointment_time = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE appointment_id = ?
                    """, (new_status, target_date, target_time, apt_id))
                else:
                    cursor.execute("""
                        UPDATE appointments
                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE appointment_id = ?
                    """, (new_status, apt_id))

                conn.commit()
                self._send_json({"success": True, "message": f"Appointment status updated to {new_status}"})
                return

            # Update Doctor Details
            if path.startswith('/api/doctors/'):
                doc_id = int(path.split('/')[-1])
                fields = []
                params = []
                for key in ['doctor_name', 'specialization', 'department', 'experience_years', 'available_days', 'room_number', 'status']:
                    if key in data:
                        fields.append(f"{key} = ?")
                        params.append(data[key])
                if not fields:
                    self._send_error("No fields to update")
                    return

                params.append(doc_id)
                cursor.execute(f"UPDATE doctors SET {', '.join(fields)} WHERE doctor_id = ?", params)
                conn.commit()
                self._send_json({"success": True, "message": "Doctor profile updated successfully"})
                return

            self._send_error("Endpoint not found", 404)

        except Exception as e:
            self._send_error(f"Update error: {str(e)}", 500)
        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Delete Doctor
            if path.startswith('/api/doctors/'):
                doc_id = int(path.split('/')[-1])
                cursor.execute("DELETE FROM doctors WHERE doctor_id = ?", (doc_id,))
                conn.commit()
                self._send_json({"success": True, "message": "Doctor removed successfully"})
                return

            # Cancel / Remove Appointment
            if path.startswith('/api/appointments/'):
                apt_id = path.split('/')[-1]
                cursor.execute("UPDATE appointments SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE appointment_id = ?", (apt_id,))
                conn.commit()
                self._send_json({"success": True, "message": "Appointment cancelled successfully"})
                return

            self._send_error("Endpoint not found", 404)

        except Exception as e:
            self._send_error(f"Deletion error: {str(e)}", 500)
        finally:
            conn.close()

def run_server(port=5000):
    init_db()
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, HospitalRequestHandler)
    print(f"===========================================================")
    print(f"  MedSchedule Hospital Backend Server Running")
    print(f"  Listening on http://0.0.0.0:{port}")
    print(f"  Database: {DB_PATH}")
    print(f"===========================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port)
