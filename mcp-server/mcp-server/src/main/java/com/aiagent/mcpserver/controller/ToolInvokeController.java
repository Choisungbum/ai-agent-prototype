package com.aiagent.mcpserver.controller;

import com.aiagent.mcpserver.model.ToolInfo;
import com.aiagent.mcpserver.service.ToolInvokeService;
import com.aiagent.mcpserver.service.ToolService;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.RequiredArgsConstructor;
import lombok.ToString;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Data
@Slf4j
@RestController
@RequestMapping("/tools")
@RequiredArgsConstructor
public class ToolInvokeController {

    @Autowired
    private final ToolInvokeService toolInvokeService;

    @GetMapping("/toolList")
    public ResponseEntity<List<ToolInfo>> getToolList(){
        List<ToolInfo> result = toolInvokeService.getToolList();
        return ResponseEntity.ok(result);
    }

    /**
     * 🧠 Tool 실행 API (공용 엔드포인트)
     * 예시 요청:
     * POST /api/tool/invoke
     * {
     *   "toolName": "select_user_list",
     *   "toolType": "DB_MAPPER"
     *   "params": {
     *       "name": "홍길동",
     *       "gender": "M",
     *       "age": 30,
     *       "ageCondition": "GT"
     *   }
     * }
     */
    @PostMapping("/invoke")
    public ResponseEntity<?> invokeTool(@RequestBody ToolInfo toolInfo) {
        try{
            // 1. toolName 추출
            // 2. toolType 추출
//            ToolInfo toolInfo = new ToolInfo();
//            toolInfo.setToolName((String) request.get("toolName"));
//            toolInfo.setToolType((String) request.get("toolType"));
//
//            // 3. params 추출 (각종 쿼리 조건, 필터 등)
//            @SuppressWarnings("unchecked")
//            Map<String, Object> params = (Map<String, Object>) request.get("params");
//
//            log.info("MCP Tool info : toolName:{}, params:{}", toolInfo.getToolName(), params);

            // 4. 서비스 레이어에 위임 (실제 DB Mapper 호출 or 비즈니스 로직 수행)
            Object result = toolInvokeService.invoke(toolInfo);

            // 5. 결과 반환
            return ResponseEntity.ok(result);
        } catch(Exception e) {
            log.error("❌ Tool Invoke Error: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "error", "Tool invocation failed",
                    "message", e.getMessage()
            ));
        }
    }


}
