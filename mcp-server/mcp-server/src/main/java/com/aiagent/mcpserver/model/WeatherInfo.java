package com.aiagent.mcpserver.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class WeatherInfo {
    private String targetDate;
    private String weather;
    private String temperature;
    private String humidity;
}
