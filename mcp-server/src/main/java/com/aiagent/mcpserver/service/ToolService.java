package com.aiagent.mcpserver.service;

import com.aiagent.mcpserver.mapper.ToolMapper;
import com.aiagent.mcpserver.model.UserJobInfo;
import com.aiagent.mcpserver.model.UserInfo;
import com.aiagent.mcpserver.model.WeatherInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ToolService {
    @Autowired
    private ToolMapper toolMapper;

    public List<UserInfo> getUserInfo(UserInfo arg) {
        return toolMapper.getUserInfo(arg);
    }

    public List<UserJobInfo> getUserJobInfo(UserJobInfo arg) {
        return toolMapper.getUserJobInfo(arg);
    }

    public List<WeatherInfo> getWeatherInfo(WeatherInfo arg) {
        return toolMapper.getWeatherInfo(arg);
    }
}
