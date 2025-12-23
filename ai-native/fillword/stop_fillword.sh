#!/bin/bash

# 检查进程是否存在
PID=$(pgrep -f "/usr/bin/python3 /root/pythonProduct/fillword/src/backend/app.py")

if [ -z "$PID" ]; then
    echo "服务未运行，无需停止"
    exit 0  # 返回 0 表示成功（即使服务未运行）
else
    echo "正在停止服务，PID: $PID"
    kill -9 "$PID"
    if [ $? -eq 0 ]; then
        echo "服务已成功停止"
        exit 0  # 成功停止
    else
        echo "停止服务失败"
        exit 1  # 返回非零表示失败
    fi
fi
