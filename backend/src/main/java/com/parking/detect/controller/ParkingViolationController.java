package com.parking.detect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.parking.detect.entity.ParkingViolation;
import com.parking.detect.entity.RoiConfig;
import com.parking.detect.service.ParkingViolationService;
import com.parking.detect.service.ReportGenerationService;
import com.parking.detect.service.RoiConfigService;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.poi.xwpf.usermodel.ParagraphAlignment;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFRun;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/violations")
@CrossOrigin(origins = "*") // Allow frontend access
public class ParkingViolationController {

    @Autowired
    private ParkingViolationService parkingViolationService;

    @Autowired
    private ReportGenerationService reportGenerationService;

    @Autowired
    private RoiConfigService roiConfigService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Python vision.py -> Spring Boot (Step 2.4)
     * Receive violation data from YOLOv8 script and save to DB
     */
    @PostMapping("/upload")
    public String uploadViolation(@RequestBody ParkingViolation violation) {
        if (violation.getDetectTime() == null) {
            violation.setDetectTime(LocalDateTime.now());
        }
        violation.setStatus(0); // 0-待复核
        parkingViolationService.save(violation);
        return "success";
    }

    /**
     * Get list of pending validations (Step 4.1)
     */
    @GetMapping("/pending")
    public List<ParkingViolation> getPendingViolations() {
        return parkingViolationService.lambdaQuery().eq(ParkingViolation::getStatus, 0).list();
    }

    /**
     * Update status (Step 4.1)
     */
    @PostMapping("/{id}/status")
    public String updateStatus(@PathVariable("id") Long id, @RequestBody Map<String, Integer> payload) {
        Integer status = payload.get("status");
        boolean updated = parkingViolationService.lambdaUpdate()
                .eq(ParkingViolation::getId, id)
                .set(ParkingViolation::getStatus, status)
                .update();
        return updated ? "success" : "fail";
    }

    /**
     * Get list of generated reports (Step 4.2)
     * Modified to optionally filter by date range for the frontend optimizations.
     */
    @GetMapping("/reports")
    public List<ParkingViolation> getReports(
            @RequestParam(name = "startDate", required = false) String startDate,
            @RequestParam(name = "endDate", required = false) String endDate) {

        LambdaQueryWrapper<ParkingViolation> query = new LambdaQueryWrapper<>();
        query.eq(ParkingViolation::getStatus, 3);
        
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        if (startDate != null && !startDate.isEmpty() && !startDate.equals("null")) {
            LocalDateTime start = LocalDateTime.parse(startDate + " 00:00:00", formatter);
            query.ge(ParkingViolation::getDetectTime, start);
        }
        if (endDate != null && !endDate.isEmpty() && !endDate.equals("null")) {
            LocalDateTime end = LocalDateTime.parse(endDate + " 23:59:59", formatter);
            query.le(ParkingViolation::getDetectTime, end);
        }
        
        query.orderByDesc(ParkingViolation::getDetectTime);
        return parkingViolationService.list(query);
    }

    /**
     * Export reports to Word document
     */
    @GetMapping("/export/word")
    public void exportWord(
            @RequestParam(name = "startDate", required = false) String startDate,
            @RequestParam(name = "endDate", required = false) String endDate,
            HttpServletResponse response) throws Exception {

        List<ParkingViolation> reports = getReports(startDate, endDate);

        try (XWPFDocument document = new XWPFDocument()) {
            XWPFParagraph title = document.createParagraph();
            title.setAlignment(ParagraphAlignment.CENTER);
            XWPFRun titleRun = title.createRun();
            titleRun.setText("校园违规停车通报汇编");
            titleRun.setBold(true);
            titleRun.setFontSize(16);

            for (ParkingViolation rp : reports) {
                XWPFParagraph p = document.createParagraph();
                XWPFRun run = p.createRun();
                run.setText("--------------------------------------------------");
                run.addBreak();
                run.setText("记录ID: " + rp.getId());
                run.addBreak();
                run.setText("通报时间: " + rp.getDetectTime());
                run.addBreak();
                run.setText("通报地点: " + rp.getLocation());
                run.addBreak();
                run.setText("设备编号: " + rp.getCameraId());
                run.addBreak();
                run.setText("通报内容:");
                run.addBreak();

                String content = rp.getReportText() != null ? rp.getReportText() : "无内容";
                String[] lines = content.split("\n");
                for (String line : lines) {
                    run.setText(line);
                    run.addBreak();
                }
            }

            response.setContentType("application/vnd.openxmlformats-officedocument.wordprocessingml.document");
            // encode filename to avoid issues
            response.setHeader("Content-Disposition", "attachment; filename=\"Reports_Export.docx\"");
            document.write(response.getOutputStream());
        }
    }

    /**
     * Trigger manual calculation of reports for confirmed violations (Step 3)
     */
    @PostMapping("/generate-reports")
    public String generateReports() {
        int count = reportGenerationService.generateReportsForConfirmedViolations();
        return "successfully generated " + count + " reports";
    }

    /**
     * Upload an image from Frontend to trigger the YOLO python script natively
     */
    @PostMapping("/upload-image")
    public ResponseEntity<String> uploadImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "roiId", required = false) Long roiId) {
        try {
            String roiParam = "";
            if (roiId != null) {
                RoiConfig config = roiConfigService.getById(roiId);
                if (config == null) {
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("上传检测失败: 所选 ROI 规则不存在");
                }
                if (config.getPointsJson() != null && !config.getPointsJson().trim().isEmpty()) {
                    Map<String, Object> roiPayload = new LinkedHashMap<>();
                    roiPayload.put("points", objectMapper.readValue(config.getPointsJson().trim(), Object.class));
                    roiPayload.put("referenceWidth", config.getReferenceWidth());
                    roiPayload.put("referenceHeight", config.getReferenceHeight());
                    roiParam = objectMapper.writeValueAsString(roiPayload);
                }
            }

            File uploadDir = new File(System.getProperty("user.dir"), "uploads");
            if (!uploadDir.exists()) uploadDir.mkdirs();
            File destTempFile = new File(uploadDir, System.currentTimeMillis() + "_" + file.getOriginalFilename());
            file.transferTo(destTempFile);

            File visionDir = new File(System.getProperty("user.dir"), "../vision").getCanonicalFile();
            File pythonExe = new File(visionDir, "venv/Scripts/python.exe");
            String pythonCmd = pythonExe.exists() ? pythonExe.getAbsolutePath() : "python";

            ProcessBuilder pb;
            if (!roiParam.isEmpty()) {
                pb = new ProcessBuilder(pythonCmd, "vision.py", "--source", destTempFile.getAbsolutePath(), "--roi", roiParam);
            } else {
                pb = new ProcessBuilder(pythonCmd, "vision.py", "--source", destTempFile.getAbsolutePath());
            }
            pb.directory(visionDir);
            pb.redirectErrorStream(true);
            
            Process process = pb.start();
            
            // 读取 Python 打印的日志，方便调试
            StringBuilder processOutput = new StringBuilder();
            try (java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println("[YOLO-Python] " + line);
                    processOutput.append(line).append(System.lineSeparator());
                }
            }
            
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                String errorMessage = processOutput.toString().trim();
                if (errorMessage.isEmpty()) {
                    errorMessage = "Python 检测进程退出码: " + exitCode;
                }
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("上传检测失败: " + errorMessage);
            }

            return ResponseEntity.ok("上传并检测完成！正在刷新列表...");
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("上传检测失败: " + e.getMessage());
        }
    }
}
