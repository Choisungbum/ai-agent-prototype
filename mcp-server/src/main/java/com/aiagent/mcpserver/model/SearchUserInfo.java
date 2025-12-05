package com.aiagent.mcpserver.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SearchUserInfo {
    private String ssn;
    private String name;
    private Integer age;
    private String gender;
    private String email;
    private String jobId;

    // 나이 범위조회 컬럼
    private String ageCondition;
}
