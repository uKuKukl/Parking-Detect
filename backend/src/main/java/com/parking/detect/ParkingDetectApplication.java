package com.parking.detect;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
@MapperScan("com.parking.detect.mapper")
public class ParkingDetectApplication {

    public static void main(String[] args) {
        SpringApplication.run(ParkingDetectApplication.class, args);
    }
}
