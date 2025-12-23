#!/bin/bash

# 启动服务并正确重定向日志
nohup /usr/bin/python3 /root/pythonProduct/fillword/src/backend/app.py >> /root/pythonProduct/fillword/logs/fillword.log 2>&1 &

# 检查进程是否启动
sleep 3  # 等待进程启动

PID=$(pgrep -f "/usr/bin/python3 /root/pythonProduct/fillword/src/backend/app.py")

echo "=====$PID====="

if [ -z "$PID" ]; then
    echo "服务启动失败! 未找到进程ID"
    exit 1
else
    echo "服务启动成功！PID: $PID"
    exit 0
fi
