import json
from pydantic import BaseModel, Field
from typing import Optional

class UserInfo(BaseModel):
    ssn :Optional[str]  = Field(None, description="사용자의 주민등록번호(******-*******)")
    name: Optional[str] = Field(None, description="사용자의 이름")
    age: Optional[int] = Field(None, description="사용자의 나이")
    gender: Optional[str] = Field(None, description="사용자의 성별 (남자 : M, 여자 : F)")
    email: Optional[str] = Field(None, description="사용자의 이메일")

class WeatherInfo(BaseModel):
    target_date: Optional[str] = Field(None, description="날씨를 조회하기위한 일자 (YYYYMMDD)")
    weather: Optional[str] = Field(None, description="조회하고자하는 일자의 날씨")
    temperature: Optional[int] = Field(None, description="조회하고자하는 일자의 온도")
    humidity: Optional[int] = Field(None, description="조회하고자하는 일자의 습도(0 ~ 100)")

class UserJobInfo(BaseModel):
    job_id: Optional[int] = Field(None, description="직업 순번")
    job_title: Optional[str] = Field(None, description="직업명 혹은 하는 일")
    salary: Optional[str] = Field(None, description="직업별 연봉 정보")

schema = UserJobInfo.model_json_schema()
print(json.dumps(schema))
# print(WeatherInfo.model_json_schema())
# print(UserJobInfo.model_json_schema())


