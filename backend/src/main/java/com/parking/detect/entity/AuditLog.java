package com.parking.detect.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("audit_log")
public class AuditLog {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long violationId;  // FK -> parking_violations.id
    private Long operatorId;   // FK -> sys_user.id (暂时写死为 1L，等集成登录后可改)
    private String action;     // CONFIRM / REJECT
    private String remark;
    private LocalDateTime actionTime;
}
