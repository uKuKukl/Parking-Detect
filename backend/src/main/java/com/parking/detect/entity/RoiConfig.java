package com.parking.detect.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("roi_config")
public class RoiConfig {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String pointsJson;
    private Integer referenceWidth;
    private Integer referenceHeight;
    private LocalDateTime createTime;
}
