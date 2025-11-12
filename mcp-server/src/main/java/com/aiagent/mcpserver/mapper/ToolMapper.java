package com.aiagent.mcpserver.mapper;

import com.aiagent.mcpserver.model.JobInfo;
import com.aiagent.mcpserver.model.ToolInfo;
import com.aiagent.mcpserver.model.UserInfo;
import com.aiagent.mcpserver.model.WeatherInfo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ToolMapper {
    /* Tool 목록 조회 */
    public List<ToolInfo> getToolList();

    public UserInfo getUserInfo(UserInfo args);
    public JobInfo getUserJobInfo(JobInfo args);
    public WeatherInfo getWeatherInfo(WeatherInfo args);

    int insertUserInfo(UserInfo args);
}
