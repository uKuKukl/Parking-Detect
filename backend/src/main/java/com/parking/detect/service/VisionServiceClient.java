package com.parking.detect.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.parking.detect.entity.ParkingViolation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.Map;

@Service
public class VisionServiceClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final boolean enabled;
    private final String baseUrl;

    public VisionServiceClient(
            ObjectMapper objectMapper,
            RestTemplateBuilder restTemplateBuilder,
            @Value("${vision.service.enabled:true}") boolean enabled,
            @Value("${vision.service.base-url:http://127.0.0.1:8001}") String baseUrl,
            @Value("${vision.service.timeout-ms:30000}") int timeoutMs) {
        this.objectMapper = objectMapper;
        this.enabled = enabled;
        this.baseUrl = baseUrl;
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofSeconds(5))
                .setReadTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }

    public boolean isEnabled() {
        return enabled && baseUrl != null && !baseUrl.isBlank();
    }

    public ParkingViolation detect(byte[] fileBytes, String originalFilename, String contentType, String roiJson, String cameraId) throws Exception {
        if (!isEnabled()) {
            throw new IllegalStateException("vision-service is disabled");
        }

        String endpoint = trimTrailingSlash(baseUrl) + "/detect";
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", buildFilePart(fileBytes, originalFilename, contentType));
        body.add("roi", roiJson == null ? "" : roiJson);
        body.add("camera_id", cameraId == null ? "" : cameraId);
        body.add("dwell_frames", "1");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<String> response = restTemplate.exchange(endpoint, HttpMethod.POST, request, String.class);
        if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
            throw new IllegalStateException("vision-service returned " + response.getStatusCode());
        }
        return toViolation(objectMapper.readValue(response.getBody(), Map.class));
    }

    private ParkingViolation toViolation(Map<?, ?> payload) {
        ParkingViolation violation = new ParkingViolation();
        violation.setDetectTime(java.time.LocalDateTime.parse(String.valueOf(payload.get("detectTime"))));
        violation.setLocation(stringValue(payload.get("location")));
        violation.setImagePath(stringValue(payload.get("imagePath")));
        violation.setCameraId(stringValue(payload.get("cameraId")));
        violation.setConfidence(doubleValue(payload.get("confidence")));
        violation.setDecisionDetails(stringValue(payload.get("decisionDetails")));
        return violation;
    }

    private HttpEntity<ByteArrayResource> buildFilePart(byte[] fileBytes, String originalFilename, String contentTypeValue) {
        ByteArrayResource resource = new ByteArrayResource(fileBytes) {
            @Override
            public String getFilename() {
                return originalFilename == null || originalFilename.isBlank() ? "upload.jpg" : originalFilename;
            }
        };

        HttpHeaders headers = new HttpHeaders();
        MediaType contentType = contentTypeValue == null
                ? MediaType.APPLICATION_OCTET_STREAM
                : MediaType.parseMediaType(contentTypeValue);
        headers.setContentType(contentType);
        return new HttpEntity<>(resource, headers);
    }

    private String trimTrailingSlash(String value) {
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }

    private String stringValue(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    private Double doubleValue(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value != null) {
            try {
                return Double.parseDouble(String.valueOf(value));
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }
}
