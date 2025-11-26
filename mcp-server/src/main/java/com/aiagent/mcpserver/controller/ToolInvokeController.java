package com.aiagent.mcpserver.controller;

import com.aiagent.mcpserver.model.JsonRpcRequest;
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
@RequestMapping("/")
@RequiredArgsConstructor
public class ToolInvokeController {

    @Autowired
    private final ToolInvokeService toolInvokeService;

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
