package com.aiagent.mcpserver.mapper;

import com.aiagent.mcpserver.model.UserJobInfo;
import com.aiagent.mcpserver.model.ToolInfo;
import com.aiagent.mcpserver.model.UserInfo;
import com.aiagent.mcpserver.model.WeatherInfo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ToolMapper {
    /* Tool 목록 조회 */
    public List<ToolInfo> initialize();

    public List<UserInfo> getUserInfo(UserInfo args);
    public List<UserJobInfo> getUserJobInfo(UserJobInfo args);
    public List<WeatherInfo> getWeatherInfo(WeatherInfo args);

    int insertUserInfo(UserInfo args);
}
