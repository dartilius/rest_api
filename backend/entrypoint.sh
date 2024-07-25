#!/bin/sh
# источник https://gist.github.com/VKen/4a86bda8f65d76d8106f68587cd64327

# завершить выполнение при возникновении ошибок или
# при прохождении не инициализированных переменных в коде
set -eu

# функция завершения работы
teardown()
{
    echo "Signal caught..."
    echo "Stopping celery multi gracefully..."

    # остановить воркеров при помощи `celery multi`
    # должны быть использованы такие же аргументы как в `celery multi start`
    celery multi stop 3 --pidfile=./celery-%n.pid --logfile=/app/logs/celery-%n%I.log

    echo "Stopped celery multi..."
    echo "Stopping last waited process"
    kill -s TERM "$child" 2> /dev/null
    echo "Stopped last waited process. Exiting..."
    exit 1
}

# запуск 3 воркеров с помощью `celery multi`
# с определённым логфайлом для использования `tail -f`
celery multi start 3 -l INFO \
    --pidfile=/app/logs/celery-%n.pid \
    --logfile=/app/logs/celery-%n%I.log

# ловим сигналы (докер посылает `SIGTERM` для завершения)
trap teardown INT TERM

# отражаем логи в консоль докера
tail -f /app/logs/celery*.log &

# записываем ИД процесса `tail` для функции завершения
child=$!

# ждём `tail -f` бесконечно и ловим сигналы извне,
# включая сигнал завершения от докера, в `ловушку`
wait "$child"