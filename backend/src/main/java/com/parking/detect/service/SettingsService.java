package com.parking.detect.service;

import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

@Service
public class SettingsService {

    private final Path PROMPT_FILE_PATH = Paths.get(System.getProperty("user.dir"), "prompt_template.txt");
    private final String DEFAULT_PROMPT = "请根据以下信息，生成一份正式、简洁的校园安全通报：时间：{{time}}，地点：{{location}}，设备：{{camera_id}}，发现电动车违规停放。要求包含事件描述、安全隐患说明、整改建议。";

    public String getPromptTemplate() {
        try {
            if (!Files.exists(PROMPT_FILE_PATH)) {
                return DEFAULT_PROMPT;
            }
            return Files.readString(PROMPT_FILE_PATH);
        } catch (IOException e) {
            return DEFAULT_PROMPT;
        }
    }

    public void savePromptTemplate(String template) {
        try {
            Files.writeString(PROMPT_FILE_PATH, template, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
