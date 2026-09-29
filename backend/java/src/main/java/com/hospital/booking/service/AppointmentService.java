package com.hospital.booking.service;

import com.hospital.booking.model.Appointment;
import com.hospital.booking.repository.AppointmentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Optional;

@Service
public class AppointmentService {

    @Autowired
    private AppointmentRepository appointmentRepository;

    @Transactional
    public Appointment bookAppointment(Appointment appointment) {
        // Double-booking check: Prevent booking if same doctor, date and time is already taken
        Optional<Appointment> existing = appointmentRepository.findActiveSlotBooking(
            appointment.getDoctorId(),
            appointment.getAppointmentDate(),
            appointment.getAppointmentTime()
        );

        if (existing.isPresent()) {
            throw new IllegalStateException("Slot Conflict: The selected time slot is already booked for this doctor. Please choose another time.");
        }

        // Generate formatted Appointment ID: APT-YYYYMMDD-XXX
        String dateStr = appointment.getAppointmentDate().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String prefix = "APT-" + dateStr + "-";
        Long count = appointmentRepository.countByDatePrefix(prefix) + 1;
        String generatedId = String.format("%s%03d", prefix, count);

        appointment.setAppointmentId(generatedId);
        appointment.setStatus("Confirmed");
        return appointmentRepository.save(appointment);
    }

    @Transactional
    public Appointment updateStatus(String appointmentId, String newStatus) {
        Appointment apt = appointmentRepository.findById(appointmentId)
            .orElseThrow(() -> new IllegalArgumentException("Appointment not found with ID: " + appointmentId));
        apt.setStatus(newStatus);
        return appointmentRepository.save(apt);
    }

    @Transactional
    public Appointment reschedule(String appointmentId, LocalDate newDate, String newTime) {
        Appointment apt = appointmentRepository.findById(appointmentId)
            .orElseThrow(() -> new IllegalArgumentException("Appointment not found with ID: " + appointmentId));

        // Check if target slot is available
        Optional<Appointment> conflict = appointmentRepository.findActiveSlotBooking(apt.getDoctorId(), newDate, newTime);
        if (conflict.isPresent() && !conflict.get().getAppointmentId().equals(appointmentId)) {
            throw new IllegalStateException("Conflict: The new slot is already booked. Please choose a different slot.");
        }

        apt.setAppointmentDate(newDate);
        apt.setAppointmentTime(newTime);
        apt.setStatus("Rescheduled");
        return appointmentRepository.save(apt);
    }
}
