package org.example.gateway.service;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class SessionService {
    private final StringRedisTemplate redisTemplate;

    public String createSession() {
        String session = UUID.randomUUID().toString();
        String key = "session:" + session;

        // chat history 초기화
        String value = "";

        // Redis에 저장 (Key: session:UUID, Value: 데이터, TTL: 30분)
        redisTemplate.opsForValue().set(key, value, Duration.ofMinutes(30));

        return session;
    }

}
