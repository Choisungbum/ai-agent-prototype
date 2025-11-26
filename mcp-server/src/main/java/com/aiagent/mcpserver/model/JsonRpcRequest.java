package com.aiagent.mcpserver.model;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.Map;

@Data
@AllArgsConstructor
public class JsonRpcRequest {
    public String jsonrpc;
    public String method;
    public Map<String, Object> params;
    public String id;
}
