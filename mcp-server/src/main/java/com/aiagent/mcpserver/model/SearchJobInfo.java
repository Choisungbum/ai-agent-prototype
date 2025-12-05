package com.aiagent.mcpserver.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SearchJobInfo {
    private String jobId;
    private String jobTitle;
    private Integer salary;

    private Integer salaryCondition;
}
