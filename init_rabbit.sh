#!/bin/bash
set -e

echo "Creating RabbitMQ user: $RABBITMQ_USER"

# Ждём готовности RabbitMQ
until rabbitmqctl list_users > /dev/null 2>&1; do
    echo "Waiting for RabbitMQ to be ready..."
    sleep 2
done

# Проверяем, существует ли пользователь
if ! rabbitmqctl list_users | grep -q "$RABBITMQ_USER"; then
    rabbitmqctl add_user "$RABBITMQ_USER" "$RABBITMQ_PASS"
    rabbitmqctl set_permissions "$RABBITMQ_USER" ".*" ".*" ".*"
    rabbitmqctl set_user_tags "$RABBITMQ_USER" administrator
    echo "User created successfully"
else
    echo "User already exists, skipping..."
fi

# Создаём файл-маркер готовности
touch /tmp/rabbitmq_ready