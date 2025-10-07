FROM nginx:1.28.0

# Копируем основной конфиг производительности
COPY nginx-main.conf /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/templates/default.conf.template
