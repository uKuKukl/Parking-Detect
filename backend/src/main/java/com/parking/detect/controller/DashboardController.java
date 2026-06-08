package com.parking.detect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.parking.detect.entity.ParkingViolation;
import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.ParkingViolationService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class DashboardController {

    @Autowired
    private ParkingViolationService parkingViolationService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping("/summary")
    public Map<String, Object> summary(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");

        LocalDate today = LocalDate.now();
        LocalDateTime todayStart = today.atStartOfDay();
        LocalDateTime tomorrowStart = today.plusDays(1).atStartOfDay();

        List<ParkingViolation> all = parkingViolationService.list();
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("todayCount", all.stream().filter(v -> between(v.getDetectTime(), todayStart, tomorrowStart)).count());
        result.put("pendingCount", all.stream().filter(v -> Objects.equals(v.getStatus(), 0)).count());
        result.put("confirmedCount", all.stream().filter(v -> Objects.equals(v.getStatus(), 1) || Objects.equals(v.getStatus(), 3)).count());
        result.put("reportCount", all.stream().filter(v -> Objects.equals(v.getStatus(), 3)).count());

        List<Map<String, Object>> trend = new ArrayList<>();
        for (int i = 6; i >= 0; i--) {
            LocalDate date = today.minusDays(i);
            LocalDateTime start = date.atStartOfDay();
            LocalDateTime end = date.plusDays(1).atStartOfDay();
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("date", date.toString());
            item.put("count", all.stream().filter(v -> between(v.getDetectTime(), start, end)).count());
            trend.add(item);
        }
        result.put("trend", trend);

        List<Map<String, Object>> cameraRanking = all.stream()
                .filter(v -> v.getCameraId() != null && !v.getCameraId().isBlank())
                .collect(Collectors.groupingBy(ParkingViolation::getCameraId, Collectors.counting()))
                .entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(8)
                .map(e -> {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("cameraId", e.getKey());
                    item.put("count", e.getValue());
                    return item;
                })
                .toList();
        result.put("cameraRanking", cameraRanking);
        result.put("locationHeatmap", buildLocationHeatmap(all));
        result.put("hourHeatmap", buildHourHeatmap(all));

        result.put("latest", parkingViolationService.lambdaQuery()
                .orderByDesc(ParkingViolation::getDetectTime)
                .last("LIMIT 8")
                .list());
        return result;
    }

    private List<Map<String, Object>> buildLocationHeatmap(List<ParkingViolation> violations) {
        return violations.stream()
                .filter(v -> v.getLocation() != null && !v.getLocation().isBlank())
                .collect(Collectors.groupingBy(v -> normalizeLocation(v.getLocation()), Collectors.counting()))
                .entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(12)
                .map(e -> {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("location", e.getKey());
                    item.put("count", e.getValue());
                    return item;
                })
                .toList();
    }

    private List<Map<String, Object>> buildHourHeatmap(List<ParkingViolation> violations) {
        Map<Integer, Long> hourCounts = violations.stream()
                .filter(v -> v.getDetectTime() != null)
                .collect(Collectors.groupingBy(v -> v.getDetectTime().getHour(), Collectors.counting()));
        List<Map<String, Object>> result = new ArrayList<>();
        for (int hour = 0; hour < 24; hour++) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("hour", String.format("%02d:00", hour));
            item.put("count", hourCounts.getOrDefault(hour, 0L));
            result.add(item);
        }
        return result;
    }

    private String normalizeLocation(String location) {
        String text = location.trim();
        int commaIndex = text.indexOf('，');
        if (commaIndex > 0) {
            text = text.substring(0, commaIndex);
        }
        int countIndex = text.indexOf("当前画面");
        if (countIndex > 0) {
            text = text.substring(0, countIndex);
        }
        return text.length() > 24 ? text.substring(0, 24) + "..." : text;
    }

    private boolean between(LocalDateTime value, LocalDateTime start, LocalDateTime end) {
        return value != null && !value.isBefore(start) && value.isBefore(end);
    }
}
