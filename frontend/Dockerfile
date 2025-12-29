# build 단계
FROM node:18-alpine AS build
WORKDIR /app

# Docker용 환경변수 선택
COPY .env.docker .env

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# run 단계
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]