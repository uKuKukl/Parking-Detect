package com.parking.detect.controller;

import com.parking.detect.service.SettingsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/settings")
@CrossOrigin(origins = "*")
public class SettingsController {

    @Autowired
    private SettingsService settingsService;

    @GetMapping("/prompt")
    public String getPromptTemplate() {
        return settingsService.getPromptTemplate();
    }

    @PostMapping("/prompt")
    public String savePromptTemplate(@RequestBody Map<String, String> payload) {
        String template = payload.get("template");
        if (template != null && !template.trim().isEmpty()) {
            settingsService.savePromptTemplate(template);
            return "success";
        }
        return "fail";
    }
}
