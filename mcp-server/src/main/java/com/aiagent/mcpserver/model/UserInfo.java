package com.aiagent.mcpserver.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserInfo {
    private String ssn;
    private String name;
    private Integer age;
    private String gender;
    private String email;
    private String jobId;

    // db에는 없지만 나이컬럼의 조건을 담기위한 파라미터
    // EQ, GT, LT
    // default EQ
    private String ageCondition = "EQ";
}
