package com.parking.detect.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("parking_violations")
public class ParkingViolation {

    @TableId(type = IdType.AUTO)
    private Long id;

    private LocalDateTime detectTime;
    private String location;
    private String imagePath;
    private String cameraId;
    private Double confidence;
    
    /**
     * 0-待复核, 1-已确认, 2-已驳回, 3-已生成报告
     */
    private Integer status;
    
    private String reportText;
    
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
