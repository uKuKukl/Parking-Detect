-- Create Database
CREATE DATABASE IF NOT EXISTS `parking_detect` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `parking_detect`;

-- Create Table
CREATE TABLE IF NOT EXISTS `parking_violations` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `detect_time` DATETIME NOT NULL COMMENT '识别到的时间',
    `location` VARCHAR(255) NOT NULL COMMENT '违规地点',
    `image_path` VARCHAR(500) NOT NULL COMMENT '截图存储的绝对或相对路径',
    `camera_id` VARCHAR(100) NOT NULL COMMENT '摄像头ID标识',
    `confidence` DOUBLE NOT NULL COMMENT '模型识别置信度',
    `status` INT NOT NULL DEFAULT 0 COMMENT '处理状态：0-待复核, 1-已确认, 2-已驳回, 3-已生成报告',
    `report_text` TEXT COMMENT '生成的通报文本',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='违规停车记录表';
