package com.parking.detect.service;

import com.parking.detect.entity.ParkingViolation;
import dev.langchain4j.model.chat.ChatLanguageModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;
import java.util.List;

@Service
public class ReportGenerationService {

    @Autowired
    private ChatLanguageModel chatLanguageModel;

    @Autowired
    private ParkingViolationService parkingViolationService;

    @Autowired
    private SettingsService settingsService;

    public int generateReportsForConfirmedViolations() {
        // Find all violations with status = 1 (Confirmed)
        List<ParkingViolation> confirmedViolations = parkingViolationService.lambdaQuery()
                .eq(ParkingViolation::getStatus, 1)
                .list();

        if (confirmedViolations.isEmpty()) {
            return 0;
        }

        String promptTemplate = settingsService.getPromptTemplate();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        int successCount = 0;
        for (ParkingViolation violation : confirmedViolations) {
            try {
                // Replace placeholders
                String timeStr = violation.getDetectTime() != null ? violation.getDetectTime().format(formatter) : "未知时间";
                String promptText = promptTemplate
                        .replace("{{time}}", timeStr)
                        .replace("{{location}}", violation.getLocation() != null ? violation.getLocation() : "未知地点")
                        .replace("{{camera_id}}", violation.getCameraId() != null ? violation.getCameraId() : "未知设备");

                // Call LLM
                String reportText = chatLanguageModel.generate(promptText);

                // Update violation
                violation.setReportText(reportText);
                violation.setStatus(3); // 3-已生成报告
                parkingViolationService.updateById(violation);
                successCount++;
            } catch (Exception e) {
                // Log and continue
                e.printStackTrace();
            }
        }
        return successCount;
    }
}
