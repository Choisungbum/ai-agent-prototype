package org.example.gateway.controller;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.example.gateway.service.SessionService;
import org.example.gateway.vo.ChatRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ChatController {

    @Autowired
    public SessionService sessionService;

    private final RestTemplate restTemplate = new RestTemplate();

    @PostMapping("/chat")
    public ResponseEntity<?> chat(@RequestBody ChatRequest request,
                                  @RequestHeader(value = "X-Session-ID", required = false) String sessionId) {

        // Agent 서버로 전달
        String agentUrl = "http://localhost:8000/chat";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Session-ID", sessionId);

        if (request != null && "SESSION_INIT".equals(request.getMessage())) {
            String sessionid =  UUID.randomUUID().toString();
            log.info("session ID : {}", sessionid);
            headers.set("X-Session-ID", sessionid);

            log.info("initialize 요청");
            HttpEntity<ChatRequest> entity = new HttpEntity<>(request, headers);

            ResponseEntity<String> response = restTemplate.postForEntity(agentUrl + "/initialize", entity, String.class);
            String body = response.getBody() == null ? "success" : response.getBody();
            log.info("initialize 결과 : {}", body);
            return ResponseEntity.ok(Map.of("session", sessionid, "response", body));
        }

        log.info("frontend 요청 수신 : {}", request.getMessage());

        try{
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
