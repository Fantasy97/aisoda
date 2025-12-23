CREATE TABLE odm_company_info (
    -- 主键和基础字段
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    creator VARCHAR(100) COMMENT '创建人',
    is_valid TINYINT(1) DEFAULT 1 COMMENT '是否有效 (1-有效, 0-无效)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updater VARCHAR(100) COMMENT '更新人',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 公司信息
    company_name VARCHAR(200) COMMENT '公司全称',
    company_address VARCHAR(500) COMMENT '公司地址',
    company_phone VARCHAR(50) COMMENT '公司联系电话',
    company_fax VARCHAR(50) COMMENT '公司传真',
    company_website VARCHAR(200) COMMENT '公司官网',
    service_400_phone VARCHAR(50) COMMENT '服务400电话',
    service_email VARCHAR(100) COMMENT '服务邮箱',
    service_qrcode VARCHAR(500) COMMENT '服务公众号二维码 (存储路径或URL)',
    
    -- ========== 类别：产品 (Product) ==========
    product_model_rule VARCHAR(100) COMMENT '产品型号规则',
    machine_serial_rule VARCHAR(100) COMMENT '机器序列号规则',
    
    -- ========== 类别：外观 (Appearance) ==========
    -- 上盖logo矢量图
    cover_logo_vector VARCHAR(500) COMMENT '上盖logo矢量图 (存储路径)',
    
    -- 上盖色板
    cover_color_plate VARCHAR(500) COMMENT '上盖色板 (存储路径)',
    
    -- 上盖色卡
    cover_color_card VARCHAR(500) COMMENT '上盖色卡 (存储路径)',
    
    -- 电气标签
    electrical_label VARCHAR(500) COMMENT '电气标签 (存储路径)',
    
    -- 纸箱
    carton VARCHAR(500) COMMENT '纸箱 (存储路径)',
    
    -- 纸箱标签
    carton_label VARCHAR(500) COMMENT '纸箱标签 (存储路径)',
    
    -- ========== 类别：副证 (Certificates) ==========
    -- CQC副证
    cqc_certificate VARCHAR(500) COMMENT 'CQC副证 (存储路径)',
    
    -- 合格证
    certificate VARCHAR(500) COMMENT '合格证 (存储路径)',
    
    -- 质保卡
    warranty_card VARCHAR(500) COMMENT '质保卡 (存储路径)',
    
    -- ========== 类别：包装 (Packaging) ==========
    -- 机器快装
    quick_install_guide VARCHAR(500) COMMENT '机器快装 (存储路径)',
    
    -- 出厂检验报告
    inspection_report VARCHAR(500) COMMENT '出厂检验报告 (存储路径)',
    
    -- 通讯棒
    communication_stick VARCHAR(500) COMMENT '通讯棒 (存储路径)',
    
    -- 其他附件包装要求
    other_packaging_requirements TEXT COMMENT '其他附件包装要求',
    
    -- ========== 类别：监控 (Monitoring) ==========
    -- 通讯协议
    communication_protocol VARCHAR(200) COMMENT '通讯协议',
    
    -- APP
    app VARCHAR(200) COMMENT 'APP',
    
    -- Cloud
    cloud VARCHAR(200) COMMENT 'Cloud',
    
    -- SIM卡
    sim_card VARCHAR(200) COMMENT 'SIM卡',
    
    -- ========== 类别：样品确认 (Sample Confirmation) ==========
    -- 空壳机
    empty_shell_machine VARCHAR(200) COMMENT '空壳机',
    
    -- 样机
    sample_machine VARCHAR(200) COMMENT '样机',
    
    -- 索引
    INDEX idx_company_name (company_name),
    INDEX idx_create_time (create_time),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ODM信息管理表（产品定制化物料和项目变更输入信息）';