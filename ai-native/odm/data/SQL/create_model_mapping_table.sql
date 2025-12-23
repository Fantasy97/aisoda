CREATE TABLE odm_bom_mapping (
    -- 主键和基础字段
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    creator VARCHAR(100) COMMENT '创建人',
    is_valid TINYINT(1) DEFAULT 1 COMMENT '是否有效 (1-有效, 0-无效)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updater VARCHAR(100) COMMENT '更新人',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 型号映射信息
    product_model VARCHAR(100) COMMENT '产品型号',
    latest_bom VARCHAR(100) COMMENT '最新BOM',
    product_series VARCHAR(100) COMMENT '产品系列',
    device_type VARCHAR(100) COMMENT '设备类型',
    
    -- 索引
    INDEX idx_product_model (product_model),
    INDEX idx_create_time (create_time),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='型号映射表';