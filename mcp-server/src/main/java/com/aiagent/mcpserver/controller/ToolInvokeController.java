package com.aiagent.mcpserver.controller;

import com.aiagent.mcpserver.model.JsonRpcRequest;
import com.aiagent.mcpserver.service.ToolInvokeService;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Data
@Slf4j
@RestController
@RequestMapping("/")
@RequiredArgsConstructor
public class ToolInvokeController {

    @Autowired
    private final ToolInvokeService toolInvokeService;

    ObjectMapper mapper = new ObjectMapper();

//    @GetMapping("/initialize")
//    public ResponseEntity<JsonRpcResponse> initialize(){
//        List<ToolInfo> result = toolInvokeService.getToolList();
//        return ResponseEntity.ok(result);
//    }

    /**
     * agent -> mcp 서버 데이터 요청 형식
     *
     * initialize 요청 형식
     * {
     *     "jsonrpc": "2.0",
     *     "id": 1,
     *     "method": "initialize",
     *     "params": {
     *       "client": "ai-agent",
     *       "version": "1.0",
     *       "capabilities": {
     *         "toolUse": true
     *       }
     *     }
     *   }
     *
     * mcp/useTool" 메서드 요청 형식
     * {
     *     "jsonrpc": "2.0",
     *     "id": 10,
     *     "method": "tools/call",
     *     "params": {
     *       "tool": "getUserInfo",
     *       "toolCallId": "call_001",
     *       "args": {
     *         "name": "홍길동"
     *       }
     *     }
     *   }
     *
     */
    @PostMapping("/invoke")
    public ResponseEntity<?> invoke(@RequestBody JsonRpcRequest request) {
        try{
            Object result = toolInvokeService.invoke(request);

            try {
//                args 조회
                Map<String, Object> params = request.getParams();
                Map<String, Object> args = (Map<String, Object>) params.get("args");
                String argsJson = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(args);
                System.out.println("##################print args : ");
                System.out.println(argsJson);

                // 2. 맵을 JSON 문자열로 변환 (writeValueAsString)
                String resultJson = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(result);
                System.out.println("##################print result : ");
                System.out.println(resultJson);
            } catch (Exception e) {
                e.printStackTrace();
            }
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
