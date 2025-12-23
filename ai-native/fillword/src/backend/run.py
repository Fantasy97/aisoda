#!/usr/bin/env python3
"""
启动脚本 - 智能Word表单填充Flask应用
使用方法: 在 src/backend 目录下运行 python run.py
"""

if __name__ == '__main__':
    from app import app, logger
    
    logger.info("🚀 智能Word表单填充服务启动")
    logger.info("🌐 访问地址: http://localhost:5000")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")