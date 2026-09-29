package com.hospital.booking.controller;

import com.hospital.booking.model.User;
import com.hospital.booking.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @Autowired
    private UserRepository userRepository;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials) {
        String identifier = credentials.get("identifier");
        String password = credentials.get("password");

        Optional<User> userOpt = userRepository.findByEmail(identifier);
        if (!userOpt.isPresent()) {
            userOpt = userRepository.findByMobile(identifier);
        }

        if (userOpt.isPresent()) {
            User user = userOpt.get();
            // Verify password (In production, use BCryptPasswordEncoder)
            Map<String, Object> resp = new HashMap<>();
            resp.put("success", true);
            resp.put("user", user);
            return ResponseEntity.ok(resp);
        }

        Map<String, Object> err = new HashMap<>();
        err.put("success", false);
        err.put("error", "Invalid credentials");
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(err);
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        if (userRepository.findByEmail(user.getEmail()).isPresent()) {
            Map<String, Object> err = new HashMap<>();
            err.put("success", false);
            err.put("error", "Email already registered");
            return ResponseEntity.status(HttpStatus.CONFLICT).body(err);
        }
        User saved = userRepository.save(user);
        Map<String, Object> resp = new HashMap<>();
        resp.put("success", true);
        resp.put("user", saved);
        return ResponseEntity.status(HttpStatus.CREATED).body(resp);
    }
}
