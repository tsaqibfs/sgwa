FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM nginx:stable-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/nginx-site.conf /etc/nginx/sgwa-site.conf
COPY frontend/nginx-api.conf /etc/nginx/sgwa-api.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
