-- 内部设计记录表
CREATE TABLE design_record (
    -- 主键和基础字段
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    creator VARCHAR(100) COMMENT '创建人',
    is_valid TINYINT(1) DEFAULT 1 COMMENT '是否有效 (1-有效, 0-无效)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updater VARCHAR(100) COMMENT '更新人',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 基本信息
    odm_bom VARCHAR(100) COMMENT 'ODM BOM',
    odm_model VARCHAR(100) COMMENT 'ODM型号',
    structure_requirement TEXT COMMENT '结构诉求',
    change_history TEXT COMMENT '变更历史',
    requirement_work_order_no JSON COMMENT '需求工单号 (数组)',
    bom_name VARCHAR(200) COMMENT 'BOM名称',
    
    -- 基础BOM信息
    base_bom_part_number VARCHAR(100) COMMENT '基础BOM料号',
    base_bom_parent_part_number VARCHAR(100) COMMENT '基础BOM上阶料号',
    base_bom_position_number VARCHAR(50) COMMENT '基础BOM位置号',
    base_bom_quantity DECIMAL(10, 2) COMMENT '基础BOM数量',
    base_bom_workstation VARCHAR(100) COMMENT '基础BOM工位',
    base_bom_description TEXT COMMENT '基础BOM说明',
    
    -- 变更BOM信息
    change_bom_part_number VARCHAR(100) COMMENT '变更BOM料号',
    change_bom_parent_part_number VARCHAR(100) COMMENT '变更BOM上阶料号',
    change_bom_position_number VARCHAR(50) COMMENT '变更BOM位置号',
    change_bom_quantity DECIMAL(10, 2) COMMENT '变更BOM数量',
    change_bom_workstation VARCHAR(100) COMMENT '变更BOM工位',
    change_operation VARCHAR(50) COMMENT '变更操作 (如: 新增/删除/修改)',
    
    -- 索引
    INDEX idx_odm_bom (odm_bom),
    INDEX idx_odm_model (odm_model),
    -- JSON字段无法直接建立普通索引，如需索引可使用生成列
    INDEX idx_base_bom_part_number (base_bom_part_number),
    INDEX idx_change_bom_part_number (change_bom_part_number),
    INDEX idx_create_time (create_time),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内部设计记录表';

