package com.parking.detect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;

import com.parking.detect.entity.AuditLog;
import com.parking.detect.entity.CameraDevice;
import com.parking.detect.entity.ParkingViolation;
import com.parking.detect.entity.RoiConfig;
import com.parking.detect.entity.SysUser;
import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.AuditLogService;
import com.parking.detect.service.CameraDeviceService;
import com.parking.detect.service.ParkingViolationService;
import com.parking.detect.service.ReportGenerationService;
import com.parking.detect.service.RoiConfigService;
import com.parking.detect.service.VisionServiceClient;
import jakarta.servlet.http.HttpSession;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.xwpf.usermodel.ParagraphAlignment;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.apache.poi.xwpf.usermodel.XWPFRun;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/violations")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class ParkingViolationController {

    @Autowired
    private ParkingViolationService parkingViolationService;

    @Autowired
    private ReportGenerationService reportGenerationService;

    @Autowired
    private RoiConfigService roiConfigService;

    @Autowired
    private AuditLogService auditLogService;

    @Autowired
    private CameraDeviceService cameraDeviceService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @Autowired
    private VisionServiceClient visionServiceClient;

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
    public List<ParkingViolation> getPendingViolations(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        return parkingViolationService.lambdaQuery().eq(ParkingViolation::getStatus, 0).list();
    }

    @GetMapping
    public Page<ParkingViolation> queryViolations(
            @RequestParam(name = "status", required = false) Integer status,
            @RequestParam(name = "cameraId", required = false) String cameraId,
            @RequestParam(name = "keyword", required = false) String keyword,
            @RequestParam(name = "startDate", required = false) String startDate,
            @RequestParam(name = "endDate", required = false) String endDate,
            @RequestParam(name = "page", defaultValue = "1") long page,
            @RequestParam(name = "size", defaultValue = "10") long size,
            HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        LambdaQueryWrapper<ParkingViolation> query = buildViolationQuery(status, cameraId, keyword, startDate, endDate);
        query.orderByDesc(ParkingViolation::getDetectTime);
        return parkingViolationService.page(new Page<>(page, size), query);
    }

    /**
     * Stream the saved YOLO annotated image for a violation record.
     */
    @GetMapping("/{id}/image")
    public ResponseEntity<?> getViolationImage(@PathVariable("id") Long id, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        ParkingViolation violation = parkingViolationService.getById(id);
        if (violation == null || violation.getImagePath() == null || violation.getImagePath().trim().isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("未找到对应图片");
        }

        File imageFile = new File(violation.getImagePath().trim());
        if (!imageFile.isAbsolute()) {
            imageFile = new File(System.getProperty("user.dir"), violation.getImagePath().trim());
        }
        imageFile = imageFile.getAbsoluteFile();

        if (!imageFile.exists() || !imageFile.isFile()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("图片文件不存在");
        }

        try {
            MediaType mediaType = resolveImageMediaType(imageFile);
            return ResponseEntity.ok()
                    .header(HttpHeaders.CACHE_CONTROL, "no-cache, no-store, must-revalidate")
                    .contentType(mediaType)
                    .body(new FileSystemResource(imageFile));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("读取图片失败");
        }
    }

    /**
     * Update status (Step 4.1) - also writes an audit_log entry
     */
    @PostMapping("/{id}/status")
    public String updateStatus(@PathVariable("id") Long id, @RequestBody Map<String, Object> payload, HttpSession session) {
        SysUser currentUser = sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        Integer status = toInteger(payload.get("status"));
        if (status == null) {
            return "fail";
        }

        ParkingViolation violation = parkingViolationService.getById(id);
        if (violation == null) {
            return "fail";
        }

        Integer manualViolationCount = toInteger(payload.get("manualViolationCount"));
        String remark = payload.containsKey("remark") ? String.valueOf(payload.get("remark")) : null;
        if (remark != null) {
            remark = remark.trim();
            if (remark.isEmpty() || "null".equalsIgnoreCase(remark)) {
                remark = null;
            }
        }

        if (status == 1) {
            Integer resolvedViolationCount = manualViolationCount;
            if (resolvedViolationCount == null) {
                resolvedViolationCount = parkingViolationService.resolveViolationCount(violation.getLocation());
            }
            if (resolvedViolationCount == null || resolvedViolationCount < 1) {
                resolvedViolationCount = 1;
            }
            violation.setLocation(parkingViolationService.buildLocationText(
                    violation.getCameraId(),
                    violation.getLocation(),
                    resolvedViolationCount
            ));
        } else if (status == 4) {
            violation.setLocation(parkingViolationService.buildLocationText(
                    violation.getCameraId(),
                    violation.getLocation(),
                    0
            ));
        }

        violation.setStatus(status);
        boolean updated = parkingViolationService.updateById(violation);

        // 写入审核日志（不影响主流程）
        if (updated) {
            try {
                AuditLog log = new AuditLog();
                log.setViolationId(id);
                log.setOperatorId(currentUser.getId());
                log.setAction(resolveAuditAction(status));
                log.setRemark(buildAuditRemark(status, manualViolationCount, remark));
                log.setActionTime(java.time.LocalDateTime.now());
                auditLogService.save(log);
            } catch (Exception logEx) {
                System.err.println("[WARN] 审核日志写入失败: " + logEx.getMessage());
            }
        }

        return updated ? "success" : "fail";
    }

    /**
     * Get list of generated reports (Step 4.2)
     * Modified to optionally filter by date range for the frontend optimizations.
     */
    @GetMapping("/reports")
    public List<ParkingViolation> getReports(
            @RequestParam(name = "startDate", required = false) String startDate,
            @RequestParam(name = "endDate", required = false) String endDate,
            @RequestParam(name = "cameraId", required = false) String cameraId,
            HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");

        LambdaQueryWrapper<ParkingViolation> query = buildViolationQuery(3, cameraId, null, startDate, endDate);
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
            @RequestParam(name = "cameraId", required = false) String cameraId,
            HttpSession session,
            HttpServletResponse response) throws Exception {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        List<ParkingViolation> reports = getReports(startDate, endDate, cameraId, session).stream()
                .sorted(Comparator.comparing(ParkingViolation::getId, Comparator.nullsLast(Long::compareTo)))
                .toList();

        try (XWPFDocument document = new XWPFDocument()) {
            XWPFParagraph title = document.createParagraph();
            title.setAlignment(ParagraphAlignment.CENTER);
            XWPFRun titleRun = title.createRun();
            titleRun.setText("校园违规停车通报汇编");
            titleRun.setBold(true);
            titleRun.setFontSize(16);

            XWPFParagraph summary = document.createParagraph();
            XWPFRun summaryRun = summary.createRun();
            summaryRun.setText("导出记录数: " + reports.size());
            summaryRun.addBreak();
            summaryRun.setText("筛选条件: " + buildExportConditionText(startDate, endDate, cameraId));
            summaryRun.addBreak();

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

                run.setText("算法判定依据:");
                run.addBreak();
                run.setText(formatDecisionDetailsForExport(rp.getDecisionDetails()));
                run.addBreak();
            }

            response.setContentType("application/vnd.openxmlformats-officedocument.wordprocessingml.document");
            // encode filename to avoid issues
            response.setHeader("Content-Disposition", "attachment; filename=\"Reports_Export.docx\"");
            document.write(response.getOutputStream());
        }
    }

    @GetMapping("/export/excel")
    public void exportExcel(
            @RequestParam(name = "startDate", required = false) String startDate,
            @RequestParam(name = "endDate", required = false) String endDate,
            @RequestParam(name = "cameraId", required = false) String cameraId,
            HttpSession session,
            HttpServletResponse response) throws Exception {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        List<ParkingViolation> reports = getReports(startDate, endDate, cameraId, session).stream()
                .sorted(Comparator.comparing(ParkingViolation::getId, Comparator.nullsLast(Long::compareTo)))
                .toList();

        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setHeader("Content-Disposition", "attachment; filename=Reports_Export.xlsx");
        try (XSSFWorkbook workbook = new XSSFWorkbook()) {
            Sheet sheet = workbook.createSheet("违规通报");
            Row header = sheet.createRow(0);
            String[] titles = {"ID", "识别时间", "设备编号", "地点", "置信度", "通报内容", "判定依据"};
            for (int i = 0; i < titles.length; i++) {
                header.createCell(i).setCellValue(titles[i]);
            }
            for (int i = 0; i < reports.size(); i++) {
                ParkingViolation rp = reports.get(i);
                Row row = sheet.createRow(i + 1);
                row.createCell(0).setCellValue(rp.getId() == null ? "" : String.valueOf(rp.getId()));
                row.createCell(1).setCellValue(rp.getDetectTime() == null ? "" : rp.getDetectTime().toString());
                row.createCell(2).setCellValue(rp.getCameraId() == null ? "" : rp.getCameraId());
                row.createCell(3).setCellValue(rp.getLocation() == null ? "" : rp.getLocation());
                row.createCell(4).setCellValue(rp.getConfidence() == null ? "" : String.valueOf(rp.getConfidence()));
                row.createCell(5).setCellValue(rp.getReportText() == null ? "" : rp.getReportText());
                row.createCell(6).setCellValue(formatDecisionDetailsForExport(rp.getDecisionDetails()));
            }
            for (int i = 0; i < titles.length; i++) {
                sheet.autoSizeColumn(i);
            }
            workbook.write(response.getOutputStream());
        }
    }

    /**
     * Trigger manual calculation of reports for confirmed violations (Step 3)
     */
    @PostMapping("/generate-reports")
    public String generateReports(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        int count = reportGenerationService.generateReportsForConfirmedViolations();
        return "successfully generated " + count + " reports";
    }

    /**
     * Upload an image from Frontend. Prefer the long-running FastAPI vision service;
     * fall back to the legacy script path when the service is not available locally.
     */
    @PostMapping("/upload-image")
    public ResponseEntity<String> uploadImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam(name = "roiId", required = false) Long roiId,
            HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        try {
            String roiParam = "";
            String cameraIdParam = "";
            if (roiId != null) {
                RoiConfig config = roiConfigService.getById(roiId);
                if (config == null) {
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("上传检测失败: 所选 ROI 规则不存在");
                }
                Map<String, Object> roiPayload = new LinkedHashMap<>();
                roiPayload.put("name", config.getName());
                roiPayload.put("referenceWidth", config.getReferenceWidth());
                roiPayload.put("referenceHeight", config.getReferenceHeight());
                if (config.getPointsJson() != null && !config.getPointsJson().trim().isEmpty()) {
                    roiPayload.put("points", objectMapper.readValue(config.getPointsJson().trim(), Object.class));
                } else {
                    roiPayload.put("points", List.of());
                }
                roiParam = objectMapper.writeValueAsString(roiPayload);

                CameraDevice cameraDevice = cameraDeviceService.lambdaQuery()
                        .eq(CameraDevice::getRoiId, roiId)
                        .last("LIMIT 1")
                        .one();
                if (cameraDevice != null && cameraDevice.getCameraId() != null && !cameraDevice.getCameraId().trim().isEmpty()) {
                    cameraIdParam = cameraDevice.getCameraId().trim();
                }
            }

            File uploadDir = new File(System.getProperty("user.dir"), "uploads");
            if (!uploadDir.exists()) uploadDir.mkdirs();
            File destTempFile = new File(uploadDir, System.currentTimeMillis() + "_" + sanitizeUploadFileName(file.getOriginalFilename()));
            byte[] uploadBytes = file.getBytes();
            file.transferTo(destTempFile);

            if (visionServiceClient.isEnabled()) {
                try {
                    ParkingViolation violation = visionServiceClient.detect(
                            uploadBytes,
                            file.getOriginalFilename(),
                            file.getContentType(),
                            roiParam,
                            cameraIdParam
                    );
                    if (violation.getDetectTime() == null) {
                        violation.setDetectTime(LocalDateTime.now());
                    }
                    violation.setStatus(0);
                    parkingViolationService.save(violation);
                    return ResponseEntity.ok("上传并通过 vision-service 检测完成！正在刷新列表...");
                } catch (Exception serviceEx) {
                    System.err.println("[WARN] vision-service 调用失败，回退到本地脚本: " + serviceEx.getMessage());
                }
            }

            File visionDir = new File(System.getProperty("user.dir"), "../vision").getCanonicalFile();
            File pythonExe = new File(visionDir, "venv/Scripts/python.exe");
            String pythonCmd = pythonExe.exists() ? pythonExe.getAbsolutePath() : "python";

            ProcessBuilder pb;
            if (!roiParam.isEmpty()) {
                if (!cameraIdParam.isEmpty()) {
                    pb = new ProcessBuilder(
                            pythonCmd,
                            "vision.py",
                            "--source", destTempFile.getAbsolutePath(),
                            "--roi", roiParam,
                            "--camera-id", cameraIdParam
                    );
                } else {
                    pb = new ProcessBuilder(pythonCmd, "vision.py", "--source", destTempFile.getAbsolutePath(), "--roi", roiParam);
                }
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

    private String buildExportConditionText(String startDate, String endDate, String cameraId) {
        return "日期范围=" + ((startDate == null || startDate.isBlank()) ? "不限" : startDate)
                + " 至 " + ((endDate == null || endDate.isBlank()) ? "不限" : endDate)
                + "，设备编号=" + ((cameraId == null || cameraId.isBlank()) ? "全部" : cameraId);
    }

    private String formatDecisionDetailsForExport(String decisionDetails) {
        if (decisionDetails == null || decisionDetails.isBlank()) {
            return "暂无算法判定依据";
        }
        try {
            Map<?, ?> details = objectMapper.readValue(decisionDetails, Map.class);
            Object algorithm = details.get("algorithm");
            Object processedFrames = details.get("processedFrames");
            Object confirmedCount = details.get("confirmedViolationCount");
            Object roiOverlap = details.get("roiOverlapThreshold");
            Object trackIou = details.get("trackIouThreshold");
            Object dwellFrames = details.get("dwellFrameThreshold");
            return "算法=" + valueOrDefault(algorithm)
                    + "；处理帧数=" + valueOrDefault(processedFrames)
                    + "；确认违规目标=" + valueOrDefault(confirmedCount)
                    + "；ROI重叠阈值=" + valueOrDefault(roiOverlap)
                    + "；IoU关联阈值=" + valueOrDefault(trackIou)
                    + "；滞留帧阈值=" + valueOrDefault(dwellFrames);
        } catch (Exception ignored) {
            return decisionDetails.length() > 500 ? decisionDetails.substring(0, 500) + "..." : decisionDetails;
        }
    }

    private String valueOrDefault(Object value) {
        return value == null ? "未知" : String.valueOf(value);
    }

    private LambdaQueryWrapper<ParkingViolation> buildViolationQuery(Integer status, String cameraId, String keyword, String startDate, String endDate) {
        LambdaQueryWrapper<ParkingViolation> query = new LambdaQueryWrapper<>();
        if (status != null) {
            query.eq(ParkingViolation::getStatus, status);
        }
        if (cameraId != null && !cameraId.isBlank()) {
            query.eq(ParkingViolation::getCameraId, cameraId.trim());
        }
        if (keyword != null && !keyword.isBlank()) {
            query.like(ParkingViolation::getLocation, keyword.trim());
        }

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        if (startDate != null && !startDate.isBlank() && !"null".equals(startDate)) {
            query.ge(ParkingViolation::getDetectTime, LocalDateTime.parse(startDate + " 00:00:00", formatter));
        }
        if (endDate != null && !endDate.isBlank() && !"null".equals(endDate)) {
            query.le(ParkingViolation::getDetectTime, LocalDateTime.parse(endDate + " 23:59:59", formatter));
        }
        return query;
    }

    private String sanitizeUploadFileName(String originalFilename) {
        String fileName = StringUtils.cleanPath(originalFilename == null ? "upload.jpg" : originalFilename);
        fileName = fileName.replaceAll("[^A-Za-z0-9._-]", "_");
        if (fileName.isBlank() || fileName.equals(".") || fileName.equals("..")) {
            return "upload.jpg";
        }
        return fileName;
    }

    private Integer toInteger(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value instanceof String text && !text.trim().isEmpty()) {
            try {
                return Integer.parseInt(text.trim());
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private String resolveAuditAction(Integer status) {
        if (status == null) {
            return "UPDATE";
        }
        return switch (status) {
            case 1 -> "CONFIRM";
            case 2 -> "REJECT";
            case 4 -> "CLEAR";
            default -> "UPDATE";
        };
    }

    private String buildAuditRemark(Integer status, Integer manualViolationCount, String remark) {
        if (status != null && status == 1 && manualViolationCount != null && manualViolationCount > 0) {
            String prefix = "人工复核确认 " + manualViolationCount + " 辆违停";
            return remark == null ? prefix : prefix + "；" + remark;
        }
        return remark;
    }

    private MediaType resolveImageMediaType(File imageFile) throws IOException {
        String contentType = Files.probeContentType(imageFile.toPath());
        if (contentType != null) {
            try {
                return MediaType.parseMediaType(contentType);
            } catch (Exception ignored) {
                // Fall through to extension-based detection.
            }
        }

        String fileName = imageFile.getName().toLowerCase();
        if (fileName.endsWith(".png")) {
            return MediaType.IMAGE_PNG;
        }
        if (fileName.endsWith(".gif")) {
            return MediaType.IMAGE_GIF;
        }
        if (fileName.endsWith(".webp")) {
            return MediaType.parseMediaType("image/webp");
        }
        return MediaType.IMAGE_JPEG;
    }
}
