package com.parking.detect.controller;

import com.parking.detect.entity.RoiConfig;
import com.parking.detect.service.RoiConfigService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/rois")
@CrossOrigin(origins = "*")
public class RoiConfigController {

    @Autowired
    private RoiConfigService roiConfigService;

    @GetMapping
    public List<RoiConfig> getAll() {
        return roiConfigService.lambdaQuery().orderByDesc(RoiConfig::getCreateTime).list();
    }

    @PostMapping
    public ResponseEntity<String> saveRoi(@RequestBody RoiConfig roiConfig) {
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

    @DeleteMapping("/{id}")
    public String deleteRoi(@PathVariable("id") Long id) {
        roiConfigService.removeById(id);
        return "success";
    }
}
