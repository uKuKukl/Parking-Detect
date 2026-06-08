package com.parking.detect.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.parking.detect.entity.ParkingViolation;

public interface ParkingViolationService extends IService<ParkingViolation> {
    String resolveBaseLocation(String cameraId, String storedLocation);

    Integer resolveViolationCount(String locationText);

    String buildLocationText(String cameraId, String storedLocation, Integer violationCount);
}
