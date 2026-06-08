package com.parking.detect.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class AutoReportService {

    @Autowired
    private ReportGenerationService reportGenerationService;

    private boolean enabled = false;
    private LocalDateTime lastRunTime;
    private int lastGeneratedCount;

    @Scheduled(cron = "0 0 18 * * ?")
    public void runDailyReport() {
        if (!enabled) {
            return;
        }
        runOnce();
    }

    public synchronized int runOnce() {
        lastGeneratedCount = reportGenerationService.generateReportsForConfirmedViolations();
        lastRunTime = LocalDateTime.now();
        return lastGeneratedCount;
    }

    public synchronized Map<String, Object> getStatus() {
        Map<String, Object> status = new LinkedHashMap<>();
        status.put("enabled", enabled);
        status.put("lastRunTime", lastRunTime);
        status.put("lastGeneratedCount", lastGeneratedCount);
        status.put("cron", "每天 18:00 自动生成已确认违规通报");
        return status;
    }

    public synchronized void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }
}
