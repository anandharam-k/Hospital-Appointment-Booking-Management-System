package com.hospital.booking.controller;

import com.hospital.booking.model.Appointment;
import com.hospital.booking.repository.AppointmentRepository;
import com.hospital.booking.service.AppointmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/appointments")
@CrossOrigin(origins = "*")
public class AppointmentController {

    @Autowired
    private AppointmentRepository appointmentRepository;

    @Autowired
    private AppointmentService appointmentService;

    @GetMapping
    public ResponseEntity<List<Appointment>> getAllAppointments(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) Long doctorId,
            @RequestParam(required = false) String date) {

        if (userId != null) {
            return ResponseEntity.ok(appointmentRepository.findByUserIdOrderByAppointmentDateDesc(userId));
        }
        if (doctorId != null && date != null) {
            return ResponseEntity.ok(appointmentRepository.findByDoctorIdAndAppointmentDate(doctorId, LocalDate.parse(date)));
        }
        return ResponseEntity.ok(appointmentRepository.findAll());
    }

    @PostMapping
    public ResponseEntity<?> bookAppointment(@RequestBody Appointment appointment) {
        try {
            Appointment booked = appointmentService.bookAppointment(appointment);
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Appointment Booked Successfully");
            response.put("appointment", booked);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (IllegalStateException e) {
            Map<String, Object> err = new HashMap<>();
            err.put("success", false);
            err.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.CONFLICT).body(err);
        } catch (Exception e) {
            Map<String, Object> err = new HashMap<>();
            err.put("success", false);
            err.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(err);
        }
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<?> updateStatus(
            @PathVariable("id") String id,
            @RequestBody Map<String, String> payload) {
        try {
            String status = payload.get("status");
            String newDate = payload.get("appointment_date");
            String newTime = payload.get("appointment_time");

            Appointment updated;
            if ("Rescheduled".equalsIgnoreCase(status) && newDate != null && newTime != null) {
                updated = appointmentService.reschedule(id, LocalDate.parse(newDate), newTime);
            } else {
                updated = appointmentService.updateStatus(id, status);
            }
            return ResponseEntity.ok(updated);
        } catch (IllegalStateException e) {
            Map<String, Object> err = new HashMap<>();
            err.put("success", false);
            err.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.CONFLICT).body(err);
        } catch (Exception e) {
            Map<String, Object> err = new HashMap<>();
            err.put("success", false);
            err.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(err);
        }
    }
}
