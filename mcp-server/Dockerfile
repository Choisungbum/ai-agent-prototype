# build 단계
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B clean package -DskipTests

# run 단계
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /build/target/mcp-server.jar mcp-server.jar
ENTRYPOINT ["java","-jar","/app/mcp-server.jar"]