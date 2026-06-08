package com.parking.detect.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.parking.detect.entity.CameraDevice;
import com.parking.detect.mapper.CameraDeviceMapper;
import org.springframework.stereotype.Service;

@Service
public class CameraDeviceService extends ServiceImpl<CameraDeviceMapper, CameraDevice> {
}
