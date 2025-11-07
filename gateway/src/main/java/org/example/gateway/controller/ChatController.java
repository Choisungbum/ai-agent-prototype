package org.example.gateway.controller;

import lombok.extern.slf4j.Slf4j;
import org.example.gateway.vo.ChatRequest;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ChatController {
    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/chat")
    public ResponseEntity<?> chat(@RequestBody ChatRequest request) {
        log.info("frontend 요청 수신 : {}", request.getMessage());

        // Agent 서버로 전달
        String agentUrl = "http://localhost:8000/chat";
        try{
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<ChatRequest> entity = new HttpEntity<>(request, headers);

            ResponseEntity<String> response = restTemplate.postForEntity(agentUrl, entity, String.class);
            log.info("Agent 서버 응답: {}", response.getBody());
            return ResponseEntity.ok(response.getBody());
        }catch ( Exception e ){
            log.error("Agent 서버 연결 실패 : {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Agent 서버 연결 실패");
        }
    }
}
