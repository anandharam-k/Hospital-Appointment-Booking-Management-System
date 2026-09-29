package com.hospital.booking;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class HospitalBookingApplication {
    public static void main(String[] args) {
        SpringApplication.run(HospitalBookingApplication.class, args);
        System.out.println("Hospital Appointment Booking System - Java Backend Started on port 8080");
    }
}
