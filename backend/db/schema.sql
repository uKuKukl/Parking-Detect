-- Create Database
CREATE DATABASE IF NOT EXISTS `parking_detect` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `parking_detect`;

-- ---------- 1. 系统用户表（无外键依赖） ----------
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username`    VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名（登录账号）',
  `password`    VARCHAR(255) NOT NULL COMMENT '加密后的密码',
  `real_name`   VARCHAR(50)  COMMENT '真实姓名',
  `role`        VARCHAR(20)  NOT NULL DEFAULT 'AUDITOR' COMMENT '角色: ADMIN-管理员, AUDITOR-审核员',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- ---------- 2. 电子围栏配置表（无外键依赖） ----------
CREATE TABLE IF NOT EXISTS `roi_config` (
  `id`               BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name`             VARCHAR(100) NOT NULL COMMENT '场景名称 (例如: 南门非机动车道)',
  `points_json`      TEXT NOT NULL COMMENT '点位数组的 JSON 格式',
  `reference_width`  INT NOT NULL COMMENT '绘制 ROI 时参考底图宽度',
  `reference_height` INT NOT NULL COMMENT '绘制 ROI 时参考底图高度',
  `create_time`      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='电子围栏配置表';

-- ---------- 3. 违规停车记录表（无外键依赖） ----------
CREATE TABLE IF NOT EXISTS `parking_violations` (
  `id`          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `detect_time` DATETIME NOT NULL COMMENT '识别到的时间',
  `location`    VARCHAR(255) NOT NULL COMMENT '违规地点',
  `image_path`  VARCHAR(500) NOT NULL COMMENT '截图存储的绝对或相对路径',
  `camera_id`   VARCHAR(100) NOT NULL COMMENT '摄像头ID标识',
  `confidence`  DOUBLE NOT NULL COMMENT '模型识别置信度',
  `decision_details` TEXT COMMENT '算法判定依据 JSON',
  `status`      INT NOT NULL DEFAULT 0 COMMENT '处理状态：0-待复核, 1-已确认违规, 2-已驳回误报, 3-已生成报告, 4-已确认正常(无违停)',
  `report_text` TEXT COMMENT '生成的通报文本',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规停车记录表';

-- ---------- 4. 摄像头设备表（依赖 roi_config） ----------
CREATE TABLE IF NOT EXISTS `camera_device` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `camera_id`   VARCHAR(100) NOT NULL UNIQUE COMMENT '设备唯一编号（与 parking_violations.camera_id 对应）',
  `name`        VARCHAR(100) NOT NULL COMMENT '摄像头部署名称（如 南门入口东侧）',
  `location`    VARCHAR(255) COMMENT '安装位置描述',
  `roi_id`      BIGINT COMMENT '关联的默认电子围栏配置 FK -> roi_config.id',
  `status`      TINYINT NOT NULL DEFAULT 1 COMMENT '设备状态: 1-在线, 0-离线',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_camera_roi` FOREIGN KEY (`roi_id`) REFERENCES `roi_config`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='摄像头设备表';

-- ---------- 5. 审核操作日志表（依赖 parking_violations 和 sys_user） ----------
CREATE TABLE IF NOT EXISTS `audit_log` (
  `id`           BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `violation_id` BIGINT NOT NULL COMMENT '关联违规记录 FK -> parking_violations.id',
  `operator_id`  BIGINT NOT NULL COMMENT '操作人 FK -> sys_user.id',
  `action`       VARCHAR(20) NOT NULL COMMENT '操作类型: CONFIRM-确认违规, REJECT-驳回误报',
  `remark`       VARCHAR(500) COMMENT '审核备注（可选）',
  `action_time`  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_audit_violation` FOREIGN KEY (`violation_id`) REFERENCES `parking_violations`(`id`),
  CONSTRAINT `fk_audit_operator`  FOREIGN KEY (`operator_id`)  REFERENCES `sys_user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规审核操作日志表';

INSERT INTO `sys_user` (`id`, `username`, `password`, `real_name`, `role`)
VALUES
  (1, 'admin', 'admin123', '系统管理员', 'ADMIN'),
  (2, 'auditor', 'auditor123', '审核员', 'AUDITOR')
ON DUPLICATE KEY UPDATE
  `password` = VALUES(`password`),
  `real_name` = VALUES(`real_name`),
  `role` = VALUES(`role`);
