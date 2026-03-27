package com.parking.detect.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.parking.detect.entity.ParkingViolation;
import com.parking.detect.mapper.ParkingViolationMapper;
import com.parking.detect.service.ParkingViolationService;
import org.springframework.stereotype.Service;

@Service
public class ParkingViolationServiceImpl extends ServiceImpl<ParkingViolationMapper, ParkingViolation> implements ParkingViolationService {
}
