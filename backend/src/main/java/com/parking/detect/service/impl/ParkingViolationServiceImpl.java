package com.parking.detect.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.parking.detect.entity.CameraDevice;
import com.parking.detect.entity.ParkingViolation;
import com.parking.detect.mapper.ParkingViolationMapper;
import com.parking.detect.service.CameraDeviceService;
import com.parking.detect.service.ParkingViolationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class ParkingViolationServiceImpl extends ServiceImpl<ParkingViolationMapper, ParkingViolation> implements ParkingViolationService {

    private static final Pattern COUNT_PATTERN = Pattern.compile("当前画面共发现\\s*(\\d+)\\s*辆违停");
    private static final Pattern COUNT_SUFFIX_PATTERN = Pattern.compile("\\s*[（(]?当前画面共发现\\s*\\d+\\s*辆违停[)）]?\\s*$");
    private static final Map<String, String> CAMERA_LOCATION_FALLBACKS = Map.of(
            "CAM_SOUTH_GATE_01", "南门自行车停放区西侧"
    );

    @Autowired
    private CameraDeviceService cameraDeviceService;

    @Override
    public String resolveBaseLocation(String cameraId, String storedLocation) {
        String sanitizedLocation = stripCountSuffix(storedLocation);
        if (hasText(sanitizedLocation)) {
            return sanitizedLocation;
        }

        if (hasText(cameraId)) {
            CameraDevice device = cameraDeviceService.lambdaQuery()
                    .eq(CameraDevice::getCameraId, cameraId.trim())
                    .last("LIMIT 1")
                    .one();
            if (device != null && hasText(device.getLocation())) {
                return device.getLocation().trim();
            }
        }

        if (hasText(cameraId)) {
            String fallbackLocation = CAMERA_LOCATION_FALLBACKS.get(cameraId.trim());
            if (hasText(fallbackLocation)) {
                return fallbackLocation;
            }
        }

        return "未知地点";
    }

    @Override
    public Integer resolveViolationCount(String locationText) {
        if (!hasText(locationText)) {
            return null;
        }

        Matcher matcher = COUNT_PATTERN.matcher(locationText);
        if (!matcher.find()) {
            return null;
        }

        try {
            return Integer.parseInt(matcher.group(1));
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    @Override
    public String buildLocationText(String cameraId, String storedLocation, Integer violationCount) {
        int safeViolationCount = violationCount != null && violationCount >= 0 ? violationCount : 0;
        return String.format("%s (当前画面共发现 %d 辆违停)",
                resolveBaseLocation(cameraId, storedLocation),
                safeViolationCount);
    }

    private String stripCountSuffix(String locationText) {
        if (!hasText(locationText)) {
            return null;
        }
        return COUNT_SUFFIX_PATTERN.matcher(locationText).replaceFirst("").trim();
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
