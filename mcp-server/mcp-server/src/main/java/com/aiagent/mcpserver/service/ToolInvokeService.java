package com.aiagent.mcpserver.service;

import com.aiagent.mcpserver.mapper.ToolMapper;
import com.aiagent.mcpserver.model.ToolInfo;
import com.aiagent.mcpserver.model.UserInfo;
import com.aiagent.mcpserver.model.WeatherInfo;
import com.aiagent.mcpserver.util.CommonUtils;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;

@Service
@RequiredArgsConstructor
public class ToolInvokeService {

    @Autowired
    private ToolMapper toolMapper;

    public List<ToolInfo> getToolList() {
        return toolMapper.getToolList();
    }

    /*
    * 3가지의 db tool 테이블 저장 방식이 있음
    *
    * 1. db tool 테이블에 쿼리를 직접적으로 넣는 경우
    *  - 운영 편의성은 좋지만 (insert만 하면 됨) 유연성과 안정성이 떨어짐
    * 2. db tool 테이블에 mapper 정보를 넣고 해당 쿼리는 mapper.xml에 정의
    *  - 운영 편의성은 떨어지지만, 유연성과 안정성이 보장됨(mybatis 의 if문 등으로 유연하게 대처 가능 )
    * 3. 혼합 구조
    *  - 위 두개를 섞어 사용
    *
    * -> 여기서는 혼합구조로 구현
    *
    * */
    public Object invoke(ToolInfo toolInfo) {

        switch (toolInfo.getToolType()) {
            case "DB":
            case "DB_MAPPER":
                return dbMapperTool(toolInfo);
            case "API":
            default:
                throw new IllegalArgumentException("Unknown toolType: " + toolInfo.getToolType());
        }
    }

    public Object dbMapperTool(ToolInfo toolInfo) {
        switch (toolInfo.getToolName().toLowerCase()) {
           case "get_user_info":
               UserInfo userInfo = new UserInfo();
               if (Objects.nonNull(toolInfo.getReqParams())) {
                   userInfo = CommonUtils.mapToObject(toolInfo.getReqParams(), UserInfo.class);
               }
                return toolMapper.getUserInfo(userInfo);
            case "get_wheather_info":
                WeatherInfo weatherInfo = new WeatherInfo();
                if (Objects.nonNull(toolInfo.getReqParams())) {
                    weatherInfo = CommonUtils.mapToObject(toolInfo.getReqParams(), WeatherInfo.class);
                    weatherInfo.setTargetDate(weatherInfo.getTargetDate().replace("-",""));
                }
                return toolMapper.getWeatherInfo(weatherInfo);
            default:
                throw new IllegalArgumentException("Unknown toolName: " + toolInfo.getToolName());
        }
    }

}

