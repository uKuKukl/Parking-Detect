package com.parking.detect.controller;

import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.SettingsService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/settings")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class SettingsController {

    @Autowired
    private SettingsService settingsService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping("/prompt")
    public String getPromptTemplate(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return settingsService.getPromptTemplate();
    }

    @GetMapping("/prompt/default")
    public String getDefaultPromptTemplate(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return settingsService.getDefaultPromptTemplate();
    }

    @PostMapping("/prompt")
    public String savePromptTemplate(@RequestBody Map<String, String> payload, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        String template = payload.get("template");
        if (template != null && !template.trim().isEmpty()) {
            settingsService.savePromptTemplate(template);
            return "success";
        }
        return "fail";
    }

    @PostMapping("/prompt/reset")
    public String resetPromptTemplate(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        settingsService.resetPromptTemplate();
        return "success";
    }
}
