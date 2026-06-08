package com.parking.detect.controller;

import com.parking.detect.entity.AuditLog;
import com.parking.detect.security.SessionPermissionService;
import com.parking.detect.service.AuditLogService;
import jakarta.servlet.http.HttpSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/audit-logs")
@CrossOrigin(originPatterns = "*", allowCredentials = "true")
public class AuditLogController {

    @Autowired
    private AuditLogService auditLogService;

    @Autowired
    private SessionPermissionService sessionPermissionService;

    @GetMapping
    public List<AuditLog> list(
            @RequestParam(name = "violationId", required = false) Long violationId,
            @RequestParam(name = "operatorId", required = false) Long operatorId,
            @RequestParam(name = "action", required = false) String action,
            HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return auditLogService.lambdaQuery()
                .eq(violationId != null, AuditLog::getViolationId, violationId)
                .eq(operatorId != null, AuditLog::getOperatorId, operatorId)
                .eq(action != null && !action.isBlank(), AuditLog::getAction, action)
                .orderByDesc(AuditLog::getActionTime)
                .list();
    }

    /**
     * 查询某条违规记录的全部审核历史
     */
    @GetMapping("/violation/{violationId}")
    public List<AuditLog> getByViolation(@PathVariable("violationId") Long violationId, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return auditLogService.lambdaQuery()
                .eq(AuditLog::getViolationId, violationId)
                .orderByAsc(AuditLog::getActionTime)
                .list();
    }

    /**
     * 查询某审核员的全部操作记录
     */
    @GetMapping("/operator/{operatorId}")
    public List<AuditLog> getByOperator(@PathVariable("operatorId") Long operatorId, HttpSession session) {
        sessionPermissionService.requireAnyRole(session, "ADMIN");
        return auditLogService.lambdaQuery()
                .eq(AuditLog::getOperatorId, operatorId)
                .orderByDesc(AuditLog::getActionTime)
                .list();
    }
}
