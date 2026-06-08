package com.parking.detect.controller;

import com.parking.detect.entity.CameraDevice;
import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.CameraDeviceService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/cameras")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class CameraDeviceController {

    @Autowired
    private CameraDeviceService cameraDeviceService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping
    public List<CameraDevice> getAll(HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return cameraDeviceService.lambdaQuery().orderByDesc(CameraDevice::getCreateTime).list();
    }

    @PostMapping
    public String save(@RequestBody CameraDevice device, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        if (device.getCreateTime() == null) device.setCreateTime(LocalDateTime.now());
        if (device.getStatus() == null) device.setStatus(1);
        cameraDeviceService.save(device);
        return "success";
    }

    @PutMapping("/{id}")
    public String update(@PathVariable("id") Long id, @RequestBody CameraDevice device, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        device.setId(id);
        cameraDeviceService.updateById(device);
        return "success";
    }

    @DeleteMapping("/{id}")
    public String delete(@PathVariable("id") Long id, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        cameraDeviceService.removeById(id);
        return "success";
    }
}
