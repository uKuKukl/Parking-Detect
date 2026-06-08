USE `parking_detect`;

ALTER TABLE `parking_violations`
  ADD COLUMN `decision_details` TEXT COMMENT '算法判定依据 JSON' AFTER `confidence`;
