CREATE TABLE `qis_scoring_results` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    
    -- 基础业务字段
    `related_order_no` VARCHAR(50) NOT NULL COMMENT '关联单号（如工单号、会话ID等）',
    `quality_check_type` VARCHAR(50) NOT NULL COMMENT '质检类型（如：工单、400电话、公众号等）',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型（必填）',
    `quality_check_record` TEXT NOT NULL COMMENT '质检记录（富文本信息，建议用TEXT）',

    -- 400 电话评分项（总分100）
    `call_standard_script_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '400-标准话术（0-15分）',
    `call_language_skill_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '400-语言技巧（0-15分）',
    `call_communication_skill_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '400-沟通技巧（0-20分）',
    `call_service_attitude_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '400-服务态度（0-25分）',
    `call_business_answer_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '400-业务解答（0-25分）',
    `call_issue_notes` VARCHAR(255) DEFAULT '' COMMENT '400问题记录（示例文本）',

    -- 公众号评分项（总分100）
    `wechat_standard_script_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '公众号-标准话术（0-20分）',
    `wechat_language_skill_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '公众号-语言技巧（0-30分）',
    `wechat_service_attitude_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '公众号-服务态度（0-20分）',
    `wechat_business_answer_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '公众号-业务解答（0-30分）',
    `wechat_issue_notes` VARCHAR(255) DEFAULT '' COMMENT '公众号问题记录（示例文本）',

    -- 工单评分项（总分100）
    `ticket_process_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '工单-流程（0-30分）',
    `ticket_basic_info_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '工单-基本信息（0-20分）',
    `ticket_issue_record_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '工单-问题记录（0-35分）',
    `ticket_shipping_detail_score` TINYINT UNSIGNED DEFAULT 0 COMMENT '工单-发货明细（0-15分）',
    `ticket_issue_notes` VARCHAR(255) DEFAULT '' COMMENT '工单问题记录（示例文本）',

    -- 责任人
    `responsible_person` VARCHAR(50) NOT NULL COMMENT '负责人（必填）',
    `created_time` DATETIME COMMENT '新建时间(YYYY-MM-DD HH:MM:SS)',

    -- 组织权限字段（支持多值，如 "张三|李四"）
    `readonly_member_user` VARCHAR(255) DEFAULT '' COMMENT '人员-普通成员-只读（格式：姓名|姓名）',
    `readwrite_member_user` VARCHAR(255) DEFAULT '' COMMENT '人员-普通成员-读写（格式：姓名|姓名）',
    `readonly_member_dept` VARCHAR(255) DEFAULT '' COMMENT '部门-普通成员-只读（格式：部门名|部门名）',
    `readwrite_member_dept` VARCHAR(255) DEFAULT '' COMMENT '部门-普通成员-读写（格式：部门名|部门名）',
    `readonly_member_group` VARCHAR(255) DEFAULT '' COMMENT '用户组-普通成员-只读（格式：组名|组名）',
    `readwrite_member_group` VARCHAR(255) DEFAULT '' COMMENT '用户组-普通成员-读写（格式：组名|组名）',
    `readonly_member_role` VARCHAR(255) DEFAULT '' COMMENT '角色-普通成员-只读（格式：角色名|角色名）',
    `readwrite_member_role` VARCHAR(255) DEFAULT '' COMMENT '角色-普通成员-读写（格式：角色名|角色名）',

    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务质检对象表';