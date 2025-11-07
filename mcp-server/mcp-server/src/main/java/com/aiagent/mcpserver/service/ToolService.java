package com.aiagent.mcpserver.service;

import com.aiagent.mcpserver.mapper.ToolMapper;
import com.aiagent.mcpserver.model.JobInfo;
import com.aiagent.mcpserver.model.UserInfo;
import com.aiagent.mcpserver.model.WeatherInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ToolService {
    @Autowired
    private ToolMapper toolMapper;

    public UserInfo getUserInfo(UserInfo arg) {
        return toolMapper.getUserInfo(arg);
    }

    public JobInfo getUserJobInfo(JobInfo arg) {
        return toolMapper.getUserJobInfo(arg);
    }

    public WeatherInfo getWeatherInfo(WeatherInfo arg) {
        return toolMapper.getWeatherInfo(arg);
    }
}
