package com.aiagent.mcpserver.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SearchWeatherInfo {
    private String targetDate;
    private String weather;
    private Integer temperature;
    private Integer humidity;

    private String temperatureCondition;
    private String humidityCondition;
}
