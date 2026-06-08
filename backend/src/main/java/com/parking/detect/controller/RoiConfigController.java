package com.parking.detect.controller;

import com.parking.detect.dto.RoiBindingRequest;
import com.parking.detect.entity.CameraDevice;
import com.parking.detect.entity.RoiConfig;
import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.CameraDeviceService;
import com.parking.detect.service.RoiConfigService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/rois")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class RoiConfigController {

    @Autowired
    private RoiConfigService roiConfigService;

    @Autowired
    private CameraDeviceService cameraDeviceService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping
    public List<RoiConfig> getAll(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN", "AUDITOR");
        return roiConfigService.lambdaQuery().orderByDesc(RoiConfig::getCreateTime).list();
    }

    @PostMapping
    public ResponseEntity<String> saveRoi(@RequestBody RoiConfig roiConfig, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        if (roiConfig.getReferenceWidth() == null || roiConfig.getReferenceWidth() <= 0
                || roiConfig.getReferenceHeight() == null || roiConfig.getReferenceHeight() <= 0) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("ROI 参考图尺寸无效");
        }
        if (roiConfig.getCreateTime() == null) {
            roiConfig.setCreateTime(LocalDateTime.now());
        }
        roiConfigService.save(roiConfig);
        return ResponseEntity.ok("success");
    }

    @PostMapping("/bind-camera")
    public ResponseEntity<RoiConfig> saveRoiWithCamera(@RequestBody RoiBindingRequest request, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        if (request.getReferenceWidth() == null || request.getReferenceWidth() <= 0
                || request.getReferenceHeight() == null || request.getReferenceHeight() <= 0) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }
        if (request.getName() == null || request.getName().trim().isEmpty()
                || request.getCameraId() == null || request.getCameraId().trim().isEmpty()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }

        RoiConfig roiConfig = new RoiConfig();
        roiConfig.setName(request.getName().trim());
        roiConfig.setPointsJson(request.getPointsJson());
        roiConfig.setReferenceWidth(request.getReferenceWidth());
        roiConfig.setReferenceHeight(request.getReferenceHeight());
        roiConfig.setCreateTime(LocalDateTime.now());
        roiConfigService.save(roiConfig);

        CameraDevice cameraDevice = cameraDeviceService.lambdaQuery()
                .eq(CameraDevice::getCameraId, request.getCameraId().trim())
                .last("LIMIT 1")
                .one();
        if (cameraDevice == null) {
            cameraDevice = new CameraDevice();
            cameraDevice.setCreateTime(LocalDateTime.now());
        }

        cameraDevice.setCameraId(request.getCameraId().trim());
        cameraDevice.setName(hasText(request.getCameraName()) ? request.getCameraName().trim() : request.getCameraId().trim());
        cameraDevice.setLocation(hasText(request.getLocation()) ? request.getLocation().trim() : request.getName().trim());
        cameraDevice.setRoiId(roiConfig.getId());
        cameraDevice.setStatus(1);

        if (cameraDevice.getId() == null) {
            cameraDeviceService.save(cameraDevice);
        } else {
            cameraDeviceService.updateById(cameraDevice);
        }

        return ResponseEntity.ok(roiConfig);
    }

    @DeleteMapping("/{id}")
    public String deleteRoi(@PathVariable("id") Long id, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        cameraDeviceService.lambdaQuery()
                .eq(CameraDevice::getRoiId, id)
                .list()
                .forEach(device -> cameraDeviceService.removeById(device.getId()));
        roiConfigService.removeById(id);
        return "success";
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
