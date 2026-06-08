package com.parking.detect.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.parking.detect.entity.AuditLog;
import com.parking.detect.mapper.AuditLogMapper;
import org.springframework.stereotype.Service;

@Service
public class AuditLogService extends ServiceImpl<AuditLogMapper, AuditLog> {
}
