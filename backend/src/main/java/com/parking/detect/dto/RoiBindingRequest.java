package com.parking.detect.dto;

import lombok.Data;

@Data
public class RoiBindingRequest {
    private String name;
    private String pointsJson;
    private Integer referenceWidth;
    private Integer referenceHeight;
    private String cameraId;
    private String cameraName;
    private String location;
}
