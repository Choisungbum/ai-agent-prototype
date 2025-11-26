package com.aiagent.mcpserver.service;

import com.aiagent.mcpserver.mapper.ToolMapper;
import com.aiagent.mcpserver.model.*;
import com.aiagent.mcpserver.util.CommonUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class ToolInvokeService {

    @Autowired
    private ToolMapper toolMapper;

    /**
     * mcp 서버 -> agent 데이터 응답 형식
     *
     * "initialize" 응답
     * {
     *     "jsonrpc": "2.0",
     *     "id": 1,
     *     "result": {
     *       "session": "sess_1234",
     *       "tools": [
     *         {
     *           "name": "getUserInfo",
     *           "desc": "사용자 정보 조회",
     *           "params": ["name", "age?"]
     *         }
     *       ]
     *     }
     *   }
     *
     * 요청(ID 101)에 대한 툴 실행 결과를 "result"에 담아 응답
     * {
     *     "jsonrpc": "2.0",
     *     "id": 101,
     *     "result": {
     *       "toolCallId": "call_abc_123",
     *       "content": {
     *         "status": "success",
     *         "data": {
     *           "userId": "gd_hong",
     *           "name": "홍길동",
     *           "age": 30,
     *           "email": "gildong@example.com",
     *           "department": "Engineering"
     *         }
     *       }
     *     }
     *   }
     *
     *
     * */
    public Object invoke(@RequestBody JsonRpcRequest request) {
        String id = request.getId();
        String method = (String) request.getMethod();
        // 최종 response json
        Map<String, Object> response = new HashMap<>();
        response.put("jsonrpc", "2.0");
        response.put("id", id);

        // result 객체 생성
        Map<String, Object> result = new HashMap<>();

        if ("initialize".equals(method)) {
            log.info("initialize 요청");
            List<ToolInfo> tools = toolMapper.initialize();

            List<Map<String, Object>> toolsForJson = new ArrayList<>();
            for (ToolInfo tool : tools) {
                Map<String, Object> toolForJson = new HashMap<>();
                toolForJson.put("name", tool.getToolName());
                toolForJson.put("desc", tool.getToolDescription());
                toolForJson.put("params", tool.getArgsSchema());

                toolsForJson.add(toolForJson);
            }

            result.put("session", System.currentTimeMillis());
            result.put("tools", toolsForJson);
       } else if ("tools/list".equals(method)) {
            log.info("tools/list");
            // tool list 조회
            List<ToolInfo> tools = toolMapper.initialize();

            List<Map<String, Object>> toolsForJson = new ArrayList<>();
            for (ToolInfo tool : tools) {
                Map<String, Object> toolForJson = new HashMap<>();
                toolForJson.put("name", tool.getToolName());
                toolForJson.put("desc", tool.getToolDescription());
                toolForJson.put("params", tool.getArgsSchema());

                toolsForJson.add(toolForJson);
            }

            result.put("session", System.currentTimeMillis());
            result.put("tools", toolsForJson);

        } else if ("tools/call".equals(method)) {
            Map<String, Object> params = request.getParams();
            String name = params.get("tool").toString();
            Map<String, Object> args = (Map<String, Object>) params.get("args");

            result.put("toolCallId", "callID");
            Map<String, Object> content = new HashMap<>();

            content.put("status", "success");
            List<Map<String, Object>> resultMap = new ArrayList<>();

            // tool 선택
            switch (name) {
                case "get_user_info":
                    if (Objects.nonNull(args)) {
                        UserInfo userInfo = CommonUtils.mapToObject(args, UserInfo.class);
                        List<UserInfo> data = toolMapper.getUserInfo(userInfo);

                        if (data != null) {
                            for (UserInfo info : data) {
                                resultMap.add(CommonUtils.objectToMap(info)); // 객체를 json 데이터로 변환
                            }
                        }
                    }
                    break;
                case "get_weather_info":
                    if (Objects.nonNull(args)) {
                        WeatherInfo weatherInfo = CommonUtils.mapToObject(args, WeatherInfo.class);
                        weatherInfo.setTargetDate(weatherInfo.getTargetDate().replace("-",""));
                        List<WeatherInfo> data = toolMapper.getWeatherInfo(weatherInfo);

                        if (data != null) {
                            for(WeatherInfo info : data){
                                resultMap.add(CommonUtils.objectToMap(info)); // 객체를 json 데이터로 변환
                            }
                        }
                    }
                    break;
                case "get_user_job_info":
                    if (Objects.nonNull(args)) {
                        UserJobInfo userJobInfo = CommonUtils.mapToObject(args, UserJobInfo.class);
                        List<UserJobInfo> data = toolMapper.getUserJobInfo(userJobInfo);

                        if (data != null) {
                            for(UserJobInfo info : data){
                                resultMap.add(CommonUtils.objectToMap(info)); // 객체를 json 데이터로 변환
                            }
                        }
                    }
                    break;
                default:
                    content.put("status", "fail");

            }
            content.put("data", resultMap);
            result.put("content", content);

        }
        response.put("result", result);

        return response;
    }

}

