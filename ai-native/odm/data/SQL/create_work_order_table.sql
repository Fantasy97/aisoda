CREATE TABLE odm_request_order (
    -- 主键和基础字段
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    creator VARCHAR(100) COMMENT '创建人',
    is_valid TINYINT(1) DEFAULT 1 COMMENT '是否有效 (1-有效, 0-无效)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updater VARCHAR(100) COMMENT '更新人',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 工单基本信息
    work_order_no VARCHAR(100) UNIQUE COMMENT '工单号',
    related_work_order_no VARCHAR(100) COMMENT '关联工单号',
    odm_code VARCHAR(200) COMMENT '客户ODM代码',
    selected_model_list JSON COMMENT '选择系列号',
    structure_requirement JSON COMMENT '结构变更描述',
    document_requirement JSON COMMENT '文档变更描述',
    
    -- 公司信息
    company_name VARCHAR(200) COMMENT '公司全称',
    company_address VARCHAR(500) COMMENT '公司地址',
    company_phone VARCHAR(50) COMMENT '公司联系电话',
    company_fax VARCHAR(50) COMMENT '公司传真',
    company_website VARCHAR(200) COMMENT '公司官网',
    service_400_phone VARCHAR(50) COMMENT '服务400电话',
    service_email VARCHAR(100) COMMENT '服务邮箱',
    service_qrcode VARCHAR(500) COMMENT '服务公众号二维码 (存储路径或URL)',
    
    -- 产品信息
    product_model_rule VARCHAR(100) COMMENT '产品型号规则',
    machine_serial_rule VARCHAR(100) COMMENT '机器序列号规则',
    
    -- 外观相关
    cover_logo_vector VARCHAR(500) COMMENT '上盖logo矢量图 (存储路径)',
    cover_color_plate VARCHAR(500) COMMENT '上盖色板 (存储路径)',
    cover_color_card VARCHAR(500) COMMENT '上盖色卡 (存储路径)',
    
    -- 标签和包装
    electrical_label VARCHAR(500) COMMENT '电气标签 (存储路径)',
    carton VARCHAR(500) COMMENT '纸箱 (存储路径)',
    carton_label VARCHAR(500) COMMENT '纸箱标签 (存储路径)',
    
    -- 证书和文档
    cqc_certificate VARCHAR(500) COMMENT 'CQC副证 (存储路径)',
    certificate VARCHAR(500) COMMENT '合格证 (存储路径)',
    warranty_card VARCHAR(500) COMMENT '质保卡 (存储路径)',
    quick_install_guide VARCHAR(500) COMMENT '机器快装 (存储路径)',
    inspection_report VARCHAR(500) COMMENT '出厂检验报告 (存储路径)',
    
    -- 附件和配件
    communication_stick VARCHAR(500) COMMENT '通讯棒 (存储路径)',
    other_packaging_requirements TEXT,
    
    -- 软件和协议
    communication_protocol VARCHAR(200) COMMENT '通讯协议',
    app VARCHAR(200) COMMENT 'APP',
    cloud VARCHAR(200) COMMENT 'Cloud',
    sim_card VARCHAR(200) COMMENT 'SIM卡',
    
    -- 特殊标识
    -- 空壳机
    empty_shell_machine VARCHAR(200) COMMENT '空壳机',
    
    -- 样机
    sample_machine VARCHAR(200) COMMENT '样机',
    
    -- 索引
    INDEX idx_work_order_no (work_order_no),
    INDEX idx_related_work_order_no (related_work_order_no),
    INDEX idx_customer_name (odm_code),
    INDEX idx_company_name (company_name),
    INDEX idx_create_time (create_time),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ODM需求工单管理表';