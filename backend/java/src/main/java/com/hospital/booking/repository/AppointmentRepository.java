package com.hospital.booking.repository;

import com.hospital.booking.model.Appointment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface AppointmentRepository extends JpaRepository<Appointment, String> {

    // Check if slot is already occupied (excluding Cancelled status)
    @Query("SELECT a FROM Appointment a WHERE a.doctorId = :doctorId AND a.appointmentDate = :date AND a.appointmentTime = :time AND a.status != 'Cancelled'")
    Optional<Appointment> findActiveSlotBooking(
        @Param("doctorId") Long doctorId,
        @Param("date") LocalDate date,
        @Param("time") String time
    );

    List<Appointment> findByUserIdOrderByAppointmentDateDesc(Long userId);

    List<Appointment> findByDoctorIdAndAppointmentDate(Long doctorId, LocalDate date);

    @Query("SELECT COUNT(a) FROM Appointment a WHERE a.appointmentId LIKE :prefix%")
    Long countByDatePrefix(@Param("prefix") String prefix);

    @Query("SELECT COUNT(a) FROM Appointment a WHERE a.appointmentDate = :today")
    Long countTodayAppointments(@Param("today") LocalDate today);

    @Query("SELECT a.status, COUNT(a) FROM Appointment a GROUP BY a.status")
    List<Object[]> countAppointmentsByStatus();
}
