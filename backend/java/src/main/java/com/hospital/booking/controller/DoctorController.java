package com.hospital.booking.controller;

import com.hospital.booking.model.Doctor;
import com.hospital.booking.repository.DoctorRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/doctors")
@CrossOrigin(origins = "*")
public class DoctorController {

    @Autowired
    private DoctorRepository doctorRepository;

    @GetMapping
    public ResponseEntity<List<Doctor>> getDoctors(
            @RequestParam(required = false) String department,
            @RequestParam(required = false, defaultValue = "active") String status) {
        if (department != null && !department.isEmpty()) {
            return ResponseEntity.ok(doctorRepository.findByDepartment(department));
        }
        return ResponseEntity.ok(doctorRepository.findByStatus(status));
    }

    @PostMapping
    public ResponseEntity<Doctor> addDoctor(@RequestBody Doctor doctor) {
        Doctor saved = doctorRepository.save(doctor);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteDoctor(@PathVariable("id") Long id) {
        doctorRepository.deleteById(id);
        return ResponseEntity.ok().build();
    }
}
