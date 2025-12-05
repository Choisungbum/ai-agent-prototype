package com.aiagent.mcpserver.mapper;

import com.aiagent.mcpserver.model.SearchJobInfo;
import com.aiagent.mcpserver.model.ToolInfo;
import com.aiagent.mcpserver.model.SearchUserInfo;
import com.aiagent.mcpserver.model.SearchWeatherInfo;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ToolMapper {
    /* Tool 목록 조회 */
    public List<ToolInfo> initialize();

    public List<SearchUserInfo> searchUsers(SearchUserInfo args);
    public List<SearchJobInfo> searchJobs(SearchJobInfo args);
    public List<SearchWeatherInfo> searchWeatherRecords(SearchWeatherInfo args);

    int insertUserInfo(SearchUserInfo args);
}
