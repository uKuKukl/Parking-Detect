-- =====================================================
-- 校园违规停车检测系统 · 数据库重建脚本
-- 执行前请确认已连接到正确的 MySQL 服务器！
-- 执行此脚本将删除所有现有数据并重建！
-- =====================================================

CREATE DATABASE IF NOT EXISTS `parking_detect`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `parking_detect`;

-- ===== 第一步：按外键依赖逆序删除旧表 =====
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `audit_log`;
DROP TABLE IF EXISTS `camera_device`;
DROP TABLE IF EXISTS `parking_violations`;
DROP TABLE IF EXISTS `roi_config`;
DROP TABLE IF EXISTS `sys_user`;
SET FOREIGN_KEY_CHECKS = 1;

-- ===== 第二步：按正确顺序重建所有表 =====

-- 1. 系统用户表（无外键依赖）
CREATE TABLE `sys_user` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username`    VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名（登录账号）',
  `password`    VARCHAR(255) NOT NULL COMMENT '密码',
  `real_name`   VARCHAR(50)  COMMENT '真实姓名',
  `role`        VARCHAR(20)  NOT NULL DEFAULT 'AUDITOR' COMMENT '角色: ADMIN-管理员, AUDITOR-审核员',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 2. 电子围栏配置表（无外键依赖）
CREATE TABLE `roi_config` (
  `id`               BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name`             VARCHAR(100) NOT NULL COMMENT '场景名称',
  `points_json`      TEXT NOT NULL COMMENT '围栏顶点坐标 JSON 数组',
  `reference_width`  INT NOT NULL DEFAULT 0 COMMENT '绘制时参考底图宽度',
  `reference_height` INT NOT NULL DEFAULT 0 COMMENT '绘制时参考底图高度',
  `create_time`      DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='电子围栏配置表';

-- 3. 违规停车记录表（无外键依赖）
CREATE TABLE `parking_violations` (
  `id`          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `detect_time` DATETIME NOT NULL COMMENT '识别时间',
  `location`    VARCHAR(255) NOT NULL COMMENT '地点描述（含违停数量信息）',
  `image_path`  VARCHAR(500) NOT NULL COMMENT '截图保存路径',
  `camera_id`   VARCHAR(100) NOT NULL COMMENT '摄像头设备编号',
  `confidence`  DOUBLE NOT NULL COMMENT '最高目标的识别置信度',
  `decision_details` TEXT COMMENT '算法判定依据 JSON',
  `status`      INT NOT NULL DEFAULT 0
                COMMENT '0=待复核, 1=已确认违规, 2=已驳回误报, 3=已生成通报, 4=已确认正常(无违停)',
  `report_text` TEXT COMMENT 'LLM 生成的通报文本',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规停车检测记录表';

-- 4. 摄像头设备表（外键依赖 roi_config）
CREATE TABLE `camera_device` (
  `id`          BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `camera_id`   VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号（对应 parking_violations.camera_id）',
  `name`        VARCHAR(100) NOT NULL COMMENT '摄像头名称',
  `location`    VARCHAR(255) COMMENT '安装位置描述',
  `roi_id`      BIGINT COMMENT '关联默认围栏规则 FK->roi_config.id',
  `status`      TINYINT NOT NULL DEFAULT 1 COMMENT '0=离线, 1=在线',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_camera_roi` FOREIGN KEY (`roi_id`) REFERENCES `roi_config`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='摄像头设备表';

-- 5. 审核操作日志表（外键依赖 parking_violations 和 sys_user）
CREATE TABLE `audit_log` (
  `id`           BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `violation_id` BIGINT NOT NULL COMMENT '关联违规记录 FK->parking_violations.id',
  `operator_id`  BIGINT NOT NULL COMMENT '操作人 FK->sys_user.id',
  `action`       VARCHAR(20) NOT NULL COMMENT 'CONFIRM=确认违规, REJECT=驳回误报, CLEAR=正常归档',
  `remark`       VARCHAR(500) COMMENT '审核备注',
  `action_time`  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_audit_violation` FOREIGN KEY (`violation_id`) REFERENCES `parking_violations`(`id`),
  CONSTRAINT `fk_audit_operator`  FOREIGN KEY (`operator_id`)  REFERENCES `sys_user`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规审核操作日志表';

-- ===== 第三步：插入系统初始数据 =====

-- 默认管理员与审核员账号（用于登录演示与审核日志外键）
INSERT INTO `sys_user` (`id`, `username`, `password`, `real_name`, `role`)
VALUES
  (1, 'admin', 'admin123', '系统管理员', 'ADMIN'),
  (2, 'auditor', 'auditor123', '审核员', 'AUDITOR');

-- =====================================================
-- 执行完毕！共 5 张业务表 + 2 条初始账号数据
-- =====================================================
