import json
from pydantic import BaseModel, Field
from typing import Optional

# 1. 사용자 검색 (MyBatis: getUserInfo)
class SearchUserInfo(BaseModel):
    ssn: Optional[str] = Field(
        None, 
        description="[검색 조건] 주민등록번호로 정확히 한 명을 찾을 때 입력 (없으면 생략)"
    )
    name: Optional[str] = Field(
        None, 
        description="[검색 조건] 이 이름을 가진 사용자들을 조회 (동명이인 포함)"
    )
    age: Optional[int] = Field(
        None, 
        description="[필터] 특정 나이인 사용자만 골라낼 때 입력 (예: 30)"
    )
    age_condition: Optional[str] = Field(
        None, 
        description="""[필터 옵션] 나이 검색 조건 코드. 
        - 'EQ': 같음 (기본값)
        - 'GT': ~보다 큼 (초과)
        - 'LT': ~보다 작음 (미만)
        - 'GE': ~이상
        - 'LE': ~이하
        사용자가 '30살 이상'이라고 하면 age=30, age_condition='GE'로 입력."""
    )
    gender: Optional[str] = Field(
        None, 
        description="[필터] 성별로 좁혀서 검색 (남자: 'M', 여자: 'F')"
    )
    email: Optional[str] = Field(
        None, 
        description="[검색 조건] 이메일 주소가 일치하는 사용자 조회"
    )

# 2. 날씨 검색 
class SearchWeatherInfo(BaseModel):
    target_date: Optional[str] = Field(
        None, description="[검색 조건] 날짜 (YYYYMMDD)"
    )
    weather: Optional[str] = Field(
        None, description="[필터] 날씨 상태 (맑음, 비, 흐림 등)"
    )
    
    # ★ 온도 조건 세트
    temperature: Optional[int] = Field(
        None, description="[검색 기준] 온도 값 (예: 25). 조건 코드와 함께 사용."
    )
    temperature_condition: Optional[str] = Field(
        None, description="[필터 옵션] 온도 조건 코드 (EQ, GT, LT, GE, LE). 예: '25도 이상' -> temp=25, cond='GE'"
    )

    # ★ 습도 조건 세트
    humidity: Optional[int] = Field(
        None, description="[검색 기준] 습도 값 (0~100). 조건 코드와 함께 사용."
    )
    humidity_condition: Optional[str] = Field(
        None, description="[필터 옵션] 습도 조건 코드 (EQ, GT, LT, GE, LE). 예: '습도 80 미만' -> hum=80, cond='LT'"
    )

# 3. 직업 검색 
class SearchJobInfo(BaseModel):
    job_id: Optional[int] = Field(
        None, description="[검색 조건] 직업 ID"
    )
    job_title: Optional[str] = Field(
        None, description="[검색 조건] 직업명 키워드 (예: 개발자)"
    )
    
    # ★ 연봉 조건 세트
    # 연봉은 숫자 비교해야 하니까 int로 받는다. 니 DB가 문자열이면 알아서 캐스팅해라.
    salary: Optional[int] = Field(
        None, description="[검색 기준] 연봉 값 (단위는 만단위, 숫자만 입력, 예: 5000)"
    )
    salary_condition: Optional[str] = Field(
        None, description="[필터 옵션] 연봉 조건 코드 (EQ, GT, LT, GE, LE). 예: '5천만원 이상' -> salary=5000, cond='GE'"
    )

schema = SearchJobInfo.model_json_schema()
print(json.dumps(schema, ensure_ascii=False, indent=2))
# print(WeatherInfo.model_json_schema())
# print(UserJobInfo.model_json_schema())


