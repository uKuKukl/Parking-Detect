package com.parking.detect.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("camera_device")
public class CameraDevice {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String cameraId;   // 对应 parking_violations.camera_id 的字符串设备编号
    private String name;
    private String location;
    private Long roiId;        // FK -> roi_config.id
    private Integer status;    // 1=在线, 0=离线
    private LocalDateTime createTime;
}
