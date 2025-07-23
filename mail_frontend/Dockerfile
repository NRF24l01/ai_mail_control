# === Сборка Vue.js ===
FROM node:24 AS builder

WORKDIR /app

# Копируем package.json и package-lock.json и устанавливаем зависимости
COPY package.json package-lock.json ./
RUN npm ci

ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

# Копируем исходники и собираем проект
COPY . .
RUN npm run build

# === Финальный образ на основе Nginx ===
FROM nginx:alpine

RUN apk add --no-cache curl

# Удаляем стандартные конфиги и копируем наш Nginx конфиг
RUN rm -rf /etc/nginx/conf.d/*
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/sites-enabled.conf

# Копируем собранные статические файлы из builder
COPY --from=builder /app/dist /usr/share/nginx/html