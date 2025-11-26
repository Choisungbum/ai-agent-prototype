package com.aiagent.mcpserver.model;

import java.time.LocalDateTime;
import java.util.Map;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ToolInfo {
    private Integer toolId;
    /** Tool 호출 이름 (예: select_user_list) */
    private String toolName;
    /** Tool 설명 */
    private String toolDescription;
    /** Tool 유형 (DB, DB_MAPPER, API, FILE 등) */
    private String toolType;
    /** 실행 대상 (SQL문 / Mapper.method / API URL) */
    private String functionName;
    /** 조건으로 사용 가능한 컬럼 목록 */
    private String argsSchema;
    /** 조건으로 사용 할 컬럼 목록 */
    private Map<String, Object> reqParams;
}
