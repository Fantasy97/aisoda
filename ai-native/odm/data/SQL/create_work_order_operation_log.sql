CREATE TABLE odm_request_order_log (
    -- 主键和基础字段
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    creator VARCHAR(100) COMMENT '创建人',
    is_valid TINYINT(1) DEFAULT 1 COMMENT '是否有效 (1-有效, 0-无效)',
    
    -- 关联信息
    origin_id BIGINT NOT NULL COMMENT '操作主表的主键ID (关联 odm_request_order.id)',
    related_work_order_no VARCHAR(100) COMMENT '关联工单号',
    
    -- 操作信息
    operator_user_id VARCHAR(100) COMMENT '操作用户ID',
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    operation_desc VARCHAR(500) COMMENT '操作描述',
    
    -- 变更信息
    changed_field_name VARCHAR(200) COMMENT '变更字段名',
    changed_value VARCHAR(500) COMMENT '变更后值',
    
    -- 索引
    INDEX idx_work_order_id (origin_id),
    INDEX idx_related_work_order_no (related_work_order_no),
    INDEX idx_operator_user_id (operator_user_id),
    INDEX idx_operation_time (operation_time),
    INDEX idx_changed_field_name (changed_field_name),
    INDEX idx_operation_desc (operation_desc)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ODM需求工单操作记录表';