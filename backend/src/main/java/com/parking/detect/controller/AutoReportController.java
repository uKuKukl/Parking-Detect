package com.parking.detect.controller;

import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.AutoReportService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auto-report")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class AutoReportController {

    @Autowired
    private AutoReportService autoReportService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping("/status")
    public Map<String, Object> status(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return autoReportService.getStatus();
    }

    @PostMapping("/enabled")
    public String setEnabled(@RequestBody Map<String, Boolean> payload, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        autoReportService.setEnabled(Boolean.TRUE.equals(payload.get("enabled")));
        return "success";
    }

    @PostMapping("/run-once")
    public Map<String, Object> runOnce(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        int count = autoReportService.runOnce();
        Map<String, Object> status = autoReportService.getStatus();
        status.put("generatedCount", count);
        return status;
    }
}
