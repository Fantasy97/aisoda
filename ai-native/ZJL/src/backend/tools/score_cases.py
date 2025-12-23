#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工单评分逻辑脚本
从热线受理.json读取案例数据，进行评分，输出符合qis_scoring_results_sample.json格式的结果
"""

import json
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pymysql


# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

# JSON字段名到数据库字段名的映射（用于重复记录检查）
FIELD_MAPPING_FOR_DUPLICATE = {
    '关联设备': 'field_glsb__c',
    '公众号用户': 'field_o1oCe__c',
    '微信昵称': 'field_3ff0E__c',
    '企微用户/群': 'field_812NN__c',
    '提报人': 'field_iywKQ__c',
    '提报人电话': 'field_93r62__c',
    '创建时间': 'create_time',
    '案例名称': 'name'
}


class CaseScorer:
    """工单案例评分器"""
    
    def __init__(self):
        """初始化评分器"""
        # 数据库连接（懒加载）
        self._db_connection = None
        
        # 评分分值配置
        self.score_config = {
            "工单-流程": {
                "max_score": 30,
                "scores": {
                    "关单、流程节点": 15, 
                    "重复记录、反审核": 15,  
                }
            },
            "工单-基本信息": {
                "max_score": 20,
                "scores": {
                    "工单信息": 5,
                    "提报人信息": 5,
                    "收件人信息": 5,  
                    "收货地址": 5,
                }
            },
            "工单-问题记录": {
                "max_score": 35,
                "scores": {
                    "故障设备信息": 20,
                    "客诉记录": 15,
                }
            },
            "工单-发货明细": {
                "max_score": 15,
                "scores": {
                    "发货明细是否合理": 15,
                }
            }
        }
    
    def _get_db_connection(self):
        """获取数据库连接（懒加载）"""
        if self._db_connection is None:
            try:
                self._db_connection = pymysql.connect(**DB_CONFIG)
            except Exception as e:
                print(f"警告: 数据库连接失败: {e}")
                return None
        return self._db_connection
    
    def close_db_connection(self):
        """关闭数据库连接"""
        if self._db_connection is not None:
            try:
                self._db_connection.close()
                self._db_connection = None
            except Exception as e:
                print(f"警告: 关闭数据库连接时出错: {e}")
    
    def _check_duplicate_record(self, case: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        检查是否存在重复记录
        
        检查条件：
        - 基础字段：关联设备、公众号用户、微信昵称、企微用户/群、提报人、提报人电话
        - 当业务类型为"热线受理"时，还需要比较负责人ID
        如果存在完全相同的记录，且当前记录的创建时间晚于其他记录，则认为是重复记录（需要扣分）
        
        Args:
            case: 案例数据字典
            
        Returns:
            tuple[bool, List[str]]: (是否重复, 重复工单号列表)
        """
        connection = self._get_db_connection()
        if connection is None:
            # 如果数据库连接失败，返回False（不扣分）
            return (False, [])
        
        # 获取当前案例的关键字段值
        current_name = case.get("案例名称", "").strip()
        if not current_name:
            return (False, [])
        
        # 获取业务类型
        business_type = str(case.get("业务类型", "")).strip() if case.get("业务类型") else ""
        # 判断是否为热线受理类型
        is_hotline = business_type in ["热线受理", "record_1Z80y__c"]
        is_replacement = business_type in ["替换发货", "default__c"]
        
        # 获取关联设备，如果为空则不判断重复工单
        associated_device = case.get("关联设备", "")
        if not associated_device or str(associated_device).strip() in ["", "null", "None"]:
            # 关联设备为空，不判断重复工单
            return (False, [])
        
        # 获取需要比较的字段值（基础字段）
        check_fields = {
            'record_type': case.get("业务类型", ""),
            'field_glsb__c': case.get("关联设备", ""),
            'field_o1oCe__c': case.get("公众号用户", ""),
            'field_3ff0E__c': case.get("微信昵称", ""),
            'field_812NN__c': case.get("企微用户/群", ""),
            'field_iywKQ__c': case.get("提报人", ""),
            'field_93r62__c': case.get("提报人电话", "")
        }
        
        # 当业务类型是热线受理时，需要比较负责人ID
        if is_hotline:
            check_fields['owner'] = case.get("负责人ID", "")

        
        # 处理空值：将空字符串、None、"null"、"None"统一处理为None
        for key, value in check_fields.items():
            if value is None:
                check_fields[key] = None
            else:
                value_str = str(value).strip()
                if value_str in ["", "null", "None"]:
                    check_fields[key] = None
                else:
                    check_fields[key] = value_str
        
        # 解析当前记录的创建时间
        current_create_time = None
        create_time_str = case.get("创建时间", "").strip()
        if create_time_str and create_time_str not in ["", "null", "None"]:
            try:
                current_create_time = datetime.strptime(create_time_str, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                pass
        
        if current_create_time is None:
            # 如果无法解析创建时间，无法判断，返回False
            return (False, [])
        
        # 计算当天0点（创建时间所在日期的0点）
        today_start = current_create_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 构建SQL查询条件
        # 需要检查所有字段完全相同的记录（字段数量根据业务类型动态变化），且排除当前记录本身
        conditions = []
        params = []
        
        for db_field, value in check_fields.items():
            if value is None:
                conditions.append(f"`{db_field}` IS NULL")
            else:
                conditions.append(f"`{db_field}` = %s")
                params.append(value)
        
        # 排除当前记录
        conditions.append("`name` != %s")
        params.append(current_name)
        
        # 构建SQL查询：查询创建时间早于当前记录且晚于当天0点的重复记录，并返回工单号
        # 只检查当天的重复工单
        conditions.append("`create_time` >= %s")
        params.append(today_start)
        conditions.append("`create_time` < %s")
        params.append(current_create_time)
        
        sql = f"""
            SELECT `name` 
            FROM `qis_cases_info`
            WHERE {' AND '.join(conditions)}
            ORDER BY `create_time` DESC
            LIMIT 10
        """
        
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            duplicate_cases = cursor.fetchall()
            
            if duplicate_cases:
                # 提取工单号列表
                duplicate_case_numbers = [row[0] for row in duplicate_cases if row and len(row) > 0]
                if duplicate_case_numbers:
                    return (True, duplicate_case_numbers)
                else:
                    return (False, [])
            else:
                return (False, [])
            
        except Exception as e:
            print(f"警告: 查询重复记录时出错: {e}")
            return (False, [])
        finally:
            cursor.close()
    
    def score_process(self, case: Dict[str, Any]) -> int:
        """
        评分：工单-流程
        评估关单、流程节点和重复记录、反审核
        """
        score = 0
        scores = self.score_config["工单-流程"]["scores"]
        
        # 检查关单、流程节点（工单状态和业务类型）
        has_process = False
        if case.get("工单状态"):
            status = str(case.get("工单状态", "")).strip()
            if status and status not in ["", "null", "None"]:
                has_process = True
        
        if case.get("业务类型"):
            record_type = str(case.get("业务类型", "")).strip()
            if record_type and record_type not in ["", "null", "None"]:
                has_process = True
        
        if has_process:
            score += scores["关单、流程节点"]
        
        # 检查重复记录、反审核
        # 查询数据库中是否存在完全相同的记录（关联设备、公众号用户、微信昵称、企微用户/群、提报人、负责人ID、提报人电话）
        # 如果存在且当前记录的创建时间靠后，则认为是重复记录，需要扣分
        is_duplicate, _ = self._check_duplicate_record(case)
        
        if not is_duplicate:
            # 不是重复记录，给分
            score += scores["重复记录、反审核"]
        # 如果是重复记录（创建时间靠后），则不给分（扣15分）
        
        return int(score)
    
    def score_basic_info(self, case: Dict[str, Any]) -> int:
        """
        评分：工单-基本信息
        评估工单信息、提报人信息、收件人信息、收货地址
        """
        score = 0
        scores = self.score_config["工单-基本信息"]["scores"]
        
        # 获取业务类型
        business_type = str(case.get("业务类型", "")).strip() if case.get("业务类型") else ""
        
        # 判断是否为热线受理类型
        is_hotline = business_type in ["热线受理", "record_1Z80y__c"]
        # 判断是否为替换发货类型
        is_replacement = business_type in ["default__c", "替换发货"]
        
        # 检查工单信息（案例名称和创建时间）
        has_ticket_info = False
        if case.get("案例名称"):
            name = str(case.get("案例名称", "")).strip()
            if name and name not in ["", "null", "None"]:
                has_ticket_info = True
        
        if case.get("创建时间"):
            create_time = str(case.get("创建时间", "")).strip()
            if create_time and create_time not in ["", "null", "None"]:
                has_ticket_info = True
        
        if case.get("设备类型"):
            create_time = str(case.get("设备类型", "")).strip()
            if create_time and create_time not in ["", "null", "None"]:
                has_ticket_info = True
        
        if has_ticket_info:
            # 热线受理类型：分数翻倍
            ticket_score = scores["工单信息"] * 2 if is_hotline else scores["工单信息"]
            score += ticket_score
        
        # 检查提报人信息（至少有一个）
        has_reporter = False
        if case.get("公众号用户") or case.get("微信昵称") or case.get("企微用户/群") or case.get("提报人"):
            has_reporter = True
        if has_reporter:
            # 热线受理类型：分数翻倍
            reporter_score = scores["提报人信息"] * 2 if is_hotline else scores["提报人信息"]
            score += reporter_score
        
        # 检查收件人信息
        if is_hotline:
            # 热线受理类型：收件人信息为0
            pass
        else:
            # 其他类型：暂时设为满分
            score += scores["收件人信息"]
        
        # 检查收货地址
        if is_hotline:
            # 热线受理类型：收货地址为0
            pass
        elif is_replacement:
            # 替换发货类型：需要检查解决方案、现场排查、发货原因
            has_solution = False
            if case.get("解决方案"):
                solution = str(case.get("解决方案", "")).strip()
                if solution and solution not in ["", "null", "None"]:
                    has_solution = True
            
            has_on_site = False
            if case.get("现场排查"):
                on_site = str(case.get("现场排查", "")).strip()
                if on_site and on_site not in ["", "null", "None"]:
                    has_on_site = True
            
            has_shipping_reason = False
            if case.get("发货原因"):
                shipping_reason = str(case.get("发货原因", "")).strip()
                if shipping_reason and shipping_reason not in ["", "null", "None"]:
                    has_shipping_reason = True
            
            # 如果三个字段都有值，才给收货地址的分数
            if has_solution and has_on_site and has_shipping_reason:
                score += scores["收货地址"]
        else:
            # 其他类型：暂时设为满分
            score += scores["收货地址"]
        
        return int(score)
    
    def score_issue_record(self, case: Dict[str, Any]) -> tuple[int, List[str]]:
        """
        评分：工单-问题记录
        评估故障设备信息和客诉记录
        简化逻辑：如果出现失误则扣掉全部分数
        
        Returns:
            (score, notes): 评分和问题描述列表
        """
        score = 0
        notes = []
        scores = self.score_config["工单-问题记录"]["scores"]
        
        # 获取业务类型
        business_type = str(case.get("业务类型", "")).strip() if case.get("业务类型") else ""
        # 判断是否为热线受理类型
        is_hotline = business_type in ["热线受理", "record_1Z80y__c"]
        
        # ========== 故障设备信息（20分）==========
        device_score = scores["故障设备信息"]  # 20分，默认满分
        
        # 1. 问题归类（必须项）- 仅热线受理类型才检查，缺失则扣全部分数（20分）
        if is_hotline:
            issue_category = str(case.get("问题归类", "")).strip() if case.get("问题归类") else ""
            if not issue_category or issue_category in ["", "null", "None"]:
                device_score = 0
                notes.append("问题归类未选择或选择错误")
            else:
                # 2. 关联设备/序列号 - 缺失则扣5分
                # 只有当问题归类以E或W开头时才检查关联设备
                issue_category_starts_with_ew = issue_category and (
                    issue_category.strip().upper().startswith('E') or 
                    issue_category.strip().upper().startswith('W')
                )
                
                if issue_category_starts_with_ew:
                    # 检查逻辑：(关联设备有值 OR 备用序号有值) AND 设备名称不为空 AND 关联产品不为空
                    has_device_or_backup = False
                    # 检查关联设备或备用序号是否有值
                    associated_device = str(case.get("关联设备", "")).strip() if case.get("关联设备") else ""
                    backup_sequence = str(case.get("备用序号", "")).strip() if case.get("备用序号") else ""
                    if (associated_device and associated_device not in ["", "null", "None"]) or \
                       (backup_sequence and backup_sequence not in ["", "null", "None"]):
                        has_device_or_backup = True
                    
                    # 检查设备名称和关联产品是否不为空
                    device_name = str(case.get("设备名称", "")).strip() if case.get("设备名称") else ""
                    related_product = str(case.get("关联产品", "")).strip() if case.get("关联产品") else ""
                    has_device_name = device_name and device_name not in ["", "null", "None"]
                    has_related_product = related_product and related_product not in ["", "null", "None"]
                    
                    # 如果(关联设备或备用序号有值)且(设备名称和关联产品都不为空)，则不扣分
                    if not (has_device_or_backup and has_device_name and has_related_product):
                        device_score -= 5
                        notes.append("关联设备未填写或填写错误")
                
                # 3. 设备类型 - 缺失则扣5分
                device_type = str(case.get("设备类型", "")).strip() if case.get("设备类型") else ""
                if not device_type or device_type in ["", "null", "None"]:
                    device_score -= 5
                    notes.append("设备类型未选择")
        else:
            # 非热线受理类型，不检查问题归类，直接检查其他项
            # 2. 关联设备/序列号 - 缺失则扣5分
            # 检查逻辑：(关联设备有值 OR 备用序号有值) AND 设备名称不为空 AND 关联产品不为空
            has_device_or_backup = False
            # 检查关联设备或备用序号是否有值
            associated_device = str(case.get("关联设备", "")).strip() if case.get("关联设备") else ""
            backup_sequence = str(case.get("备用序号", "")).strip() if case.get("备用序号") else ""
            if (associated_device and associated_device not in ["", "null", "None"]) or \
               (backup_sequence and backup_sequence not in ["", "null", "None"]):
                has_device_or_backup = True
            
            # 检查设备名称和关联产品是否不为空
            device_name = str(case.get("设备名称", "")).strip() if case.get("设备名称") else ""
            related_product = str(case.get("关联产品", "")).strip() if case.get("关联产品") else ""
            has_device_name = device_name and device_name not in ["", "null", "None"]
            has_related_product = related_product and related_product not in ["", "null", "None"]
            
            # 如果(关联设备或备用序号有值)且(设备名称和关联产品都不为空)，则不扣分
            if not (has_device_or_backup and has_device_name and has_related_product):
                device_score -= 5
                notes.append("关联设备未填写或填写错误")
            
            # 3. 设备类型 - 缺失则扣5分
            device_type = str(case.get("设备类型", "")).strip() if case.get("设备类型") else ""
            if not device_type or device_type in ["", "null", "None"]:
                device_score -= 5
                notes.append("设备类型未选择")
        
        # 确保分数不为负数
        device_score = max(0, device_score)
        score += device_score
        
        # ========== 客诉记录（15分）==========
        complaint_score = scores["客诉记录"]  # 15分，默认满分
        
        # 1. 问题记录（必须项）- 缺失或不完整则扣15分
        issue_record = str(case.get("问题记录", "")).strip()
        if not issue_record or issue_record in ["", "null", "None"]:
            complaint_score -= 15
            notes.append("问题记录不详细/不完整")
        elif len(issue_record) < 10:
            # 问题记录太短，扣15分
            complaint_score -= 15
            notes.append("问题记录太短")
        else:
            # 2. 问题类型（必须项）- 仅热线受理类型才检查，缺失则扣5分
            if is_hotline:
                issue_type = str(case.get("问题类型", "")).strip() if case.get("问题类型") else ""
                if not issue_type or issue_type in ["", "null", "None"]:
                    complaint_score -= 5
                    notes.append("问题类型选择错误或未选择")
                
                # 2.1 问题归类一致性检查 - 如果问题归类不为空，检查问题记录中是否包含相关内容
                # issue_category = str(case.get("问题归类", "")).strip() if case.get("问题归类") else ""
                # if issue_category and issue_category not in ["", "null", "None"]:
                #     # 提取问题归类中的关键部分进行匹配
                #     # 格式可能是 "IN00-设备不发电" 或编码格式
                #     category_in_record = False
                    
                #     # 方法1: 直接检查问题归类是否在问题记录中
                #     if issue_category in issue_record:
                #         category_in_record = True
                #     else:
                #         # 方法2: 如果问题归类包含 "-"，提取前后两部分分别检查
                #         if "-" in issue_category:
                #             parts = issue_category.split("-", 1)
                #             # 检查代码部分（如 "IN00"）
                #             if len(parts) > 0 and parts[0].strip() and parts[0].strip() in issue_record:
                #                 category_in_record = True
                #             # 检查描述部分（如 "设备不发电"）
                #             if not category_in_record and len(parts) > 1 and parts[1].strip() and parts[1].strip() in issue_record:
                #                 category_in_record = True
                #         else:
                #             # 方法3: 提取问题归类中的字母数字组合（如从 "IN00-设备不发电" 提取 "IN00"）
                #             code_match = re.search(r'([A-Z]{2,}\d+)', issue_category, re.IGNORECASE)
                #             if code_match and code_match.group(1) in issue_record:
                #                 category_in_record = True
                    
                #     if not category_in_record:
                #         complaint_score -= 5
                #         notes.append(f"问题记录中未包含问题归类相关内容（问题归类：{issue_category}）")
            
            # 3. 关键信息完整性 - 如果缺少关键信息，扣10分
            # 检查故障代码：支持 E\d+, W\d+, IN\d+, MO\d+, EV\d+, Error 等格式
            has_fault_code = bool(
                re.search(r'\b[EW]\d+', issue_record, re.IGNORECASE) or  # E01, W30 等
                re.search(r'\bIN\d+', issue_record, re.IGNORECASE) or     # IN00, IN01 等
                re.search(r'\bMO\d+', issue_record, re.IGNORECASE) or    # MO01, MO02 等
                re.search(r'\bEV\d+', issue_record, re.IGNORECASE) or    # EV01, EV02 等
                re.search(r'\bError\s+[A-Z0-9]+', issue_record, re.IGNORECASE)  # Error GND, Error ES 等
            )
            has_serial = bool(re.search(r'\b(TA|SP|CN|TB|TC|TD|TE|TF|TG|TH|TI|TJ|TK|TL|TM|TN|TO|TP|TQ|TR|TS|TT|TU|TV|TW|TX|TY|TZ)\d+', issue_record, re.IGNORECASE))
            has_key_phrases = any(phrase in issue_record for phrase in ["排查", "检查", "测试", "测量", "信号值", "累计电量", "并网时长", "故障代码", "序列号", "采集器", "低效", "安规","离线", "人为", "升级"])
            
            # 特殊判断：当内容中出现"销售"时，默认不扣分，但需要在notes中备注
            has_sales = "销售" in issue_record
            # 特殊判断：当内容中出现"无故障"时，默认不扣分，但需要在notes中备注
            has_normal = "无故障" in issue_record
            
            # 如果缺少关键信息，扣10分
            if not (has_fault_code or has_serial or has_key_phrases):
                if has_sales:
                    # 包含"销售"关键词，不扣分但备注
                    notes.append("销售发货需求，已跳过关键信息检查")
                elif has_normal:
                    # 包含"无故障"关键词，不扣分但备注
                    notes.append("无故障，已跳过关键信息检查")
                else:
                    # 不包含特殊判断，正常扣分
                    complaint_score -= 10
                    notes.append("未写关键信息（故障代码、序列号、排查步骤等）")
        
        # 确保分数不为负数
        complaint_score = max(0, complaint_score)
        score += complaint_score
        
        return (int(score), notes)
    
    def score_shipping_detail(self, case: Dict[str, Any]) -> int:
        """
        评分：工单-发货明细
        评估发货明细是否合理
        仅业务类型为"替换发货"时判断，其他类型默认满分
        """
        scores = self.score_config["工单-发货明细"]["scores"]
        
        # 获取业务类型
        business_type = str(case.get("业务类型", "")).strip() if case.get("业务类型") else ""
        # 判断是否为替换发货类型
        is_replacement = business_type in ["default__c", "替换发货"]
        
        # 如果不是替换发货类型，默认满分
        if not is_replacement:
            return int(scores["发货明细是否合理"])
        
        # 替换发货类型才进行判断
        score = scores["发货明细是否合理"]  # 默认满分
        
        # 检查发货原因和解决方案
        shipping_reason = str(case.get("发货原因", "")).strip() if case.get("发货原因") else ""
        solution = str(case.get("解决方案", "")).strip() if case.get("解决方案") else ""
        
        # 如果没有发货原因和解决方案，扣全部分数
        if (not shipping_reason or shipping_reason in ["", "null", "None"]) and \
           (not solution or solution in ["", "null", "None"]):
            score = 0
            return int(score)
        
        # 发货原因与解决方案的规则映射
        # 格式：{
        #   发货原因关键词: {
        #       "solution_required": [解决方案必须包含的关键词列表],
        #       "match_mode": "any" | "all",  # "any"表示包含任一关键词即可，"all"表示必须包含所有关键词
        #       "error_msg": "错误描述"
        #   }
        # }
        shipping_rules = {
            "故障更换": {
                "solution_required": ["换", "发"],
                "match_mode": "any",  # 包含任一关键词即可
                "error_msg": "发货原因为'故障更换'时，解决方案必须包含'换机'"
            },
            # 后续可以在这里添加更多规则，例如：
            # "信号值弱": {
            #     "solution_required": ["采集器", "信号"],
            #     "match_mode": "any",  # 包含"采集器"或"信号"任一即可
            #     "error_msg": "发货原因为'信号值弱'时，解决方案必须包含'采集器'或'信号'"
            # },
            # "配件更换": {
            #     "solution_required": ["直流端子", "交流端子"],
            #     "match_mode": "all",  # 必须同时包含"直流端子"和"交流端子"
            #     "error_msg": "发货原因为'配件更换'时，解决方案必须同时包含'直流端子'和'交流端子'"
            # },
        }
        
        # 检查所有规则
        if shipping_reason and shipping_reason not in ["", "null", "None"]:
            for reason_keyword, rule in shipping_rules.items():
                if reason_keyword in shipping_reason:
                    # 检查解决方案是否满足要求
                    if not solution or solution in ["", "null", "None"]:
                        # 没有解决方案，扣全部分数
                        score = 0
                        break
                    else:
                        # 检查解决方案是否包含必需的关键词
                        solution_required = rule.get("solution_required", [])
                        match_mode = rule.get("match_mode", "any")  # 默认使用"any"模式
                        
                        if solution_required:
                            if match_mode == "all":
                                # 必须包含所有关键词
                                if not all(keyword in solution for keyword in solution_required):
                                    # 解决方案不包含所有必需关键词，扣全部分数
                                    score = 0
                                    break
                            else:
                                # 默认"any"模式：包含任一关键词即可
                                if not any(keyword in solution for keyword in solution_required):
                                    # 解决方案不包含任一必需关键词，扣全部分数
                                    score = 0
                                    break
        
        return int(score)
    
    def generate_quality_record(self, case: Dict[str, Any], scores: Dict[str, int]) -> str:
        """
        生成质检记录描述
        """
        parts = []
        
        # 检查是否为重复工单，如果是，在开头添加提示
        is_duplicate, duplicate_case_numbers = self._check_duplicate_record(case)
        if is_duplicate:
            if duplicate_case_numbers:
                # 显示重复工单号（最多显示3个）
                display_numbers = duplicate_case_numbers[:3]
                duplicate_info = "、".join(display_numbers)
                if len(duplicate_case_numbers) > 3:
                    duplicate_info += f"等{len(duplicate_case_numbers)}个"
                parts.append(f"重复工单：重复创建咨询工单（重复工单号：{duplicate_info}）")
            else:
                parts.append("重复工单：重复创建咨询工单")
        
        # 基本信息
        if case.get("问题记录"):
            issue = str(case.get("问题记录", ""))[:50]  # 截取前50字
            parts.append(f"问题记录：{issue}")
        
        # 评分情况
        score_parts = []
        if scores.get("工单-流程", 0) > 0:
            score_parts.append(f"流程评分{scores['工单-流程']}分")
        if scores.get("工单-基本信息", 0) > 0:
            score_parts.append(f"基本信息评分{scores['工单-基本信息']}分")
        if scores.get("工单-问题记录", 0) > 0:
            score_parts.append(f"问题记录评分{scores['工单-问题记录']}分")
        if scores.get("工单-发货明细", 0) > 0:
            score_parts.append(f"发货明细评分{scores['工单-发货明细']}分")
        
        if score_parts:
            parts.append("，".join(score_parts))
        
        return "，".join(parts) if parts else "工单信息填写完整，各项评分正常。"
    
    def generate_issue_notes(self, case: Dict[str, Any], scores: Dict[str, int], issue_record_notes: List[str] = None) -> str:
        """
        生成工单问题记录描述
        
        Args:
            case: 案例数据字典
            scores: 各项评分字典
            issue_record_notes: 问题记录的具体问题描述列表
        """
        notes = []
        
        # 检查是否为重复工单，如果是，在开头添加提示
        is_duplicate, duplicate_case_numbers = self._check_duplicate_record(case)
        if is_duplicate:
            if duplicate_case_numbers:
                # 显示重复工单号（最多显示3个）
                display_numbers = duplicate_case_numbers[:3]
                duplicate_info = "、".join(display_numbers)
                if len(duplicate_case_numbers) > 3:
                    duplicate_info += f"等{len(duplicate_case_numbers)}个"
                notes.append(f"重复工单：重复创建咨询工单（重复工单号：{duplicate_info}）")
            else:
                notes.append("重复工单：重复创建咨询工单")
            
        # 检查各项得分情况（阈值设为满分的60%）
        if scores.get("工单-流程", 0) < 18:  # 30 * 0.6 = 18
            notes.append("工单流程信息需要完善")
        
        if scores.get("工单-基本信息", 0) < 12:  # 20 * 0.6 = 12
            notes.append("基本信息填写不完整")
        
        # 添加问题记录的具体问题描述
        if issue_record_notes:
            notes.extend(issue_record_notes)
        elif scores.get("工单-问题记录", 0) < 21:  # 35 * 0.6 = 21
            # 如果没有具体的问题描述，使用通用描述
            notes.append("问题记录需要更详细")
        
        if scores.get("工单-发货明细", 0) < 9:  # 15 * 0.6 = 9
            notes.append("发货明细信息缺失")
        
        if not notes:
            total_score = sum(scores.values())
            if total_score >= 90:  # 总分100，90分以上为优秀
                return "工单处理流程规范，信息完整，评分优秀"
            elif total_score >= 80:  # 80分以上为良好
                return "工单处理流程规范，信息完整"
            else:
                return "工单信息基本完整，部分细节需要完善"
        
        return "，".join(notes)
    
    def get_responsible_person(self, case: Dict[str, Any]) -> str:
        """
        获取负责人姓名（从负责人ID转换，这里简化处理）
        """
        owner_id = "于泽斌";
        if owner_id:
            # 这里应该通过API查询负责人姓名，暂时返回ID
            # 实际使用时需要调用纷享销客API获取用户信息
            return owner_id
        return "未知"
    
    def score_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单个案例进行评分
        
        Args:
            case: 案例数据字典
            
        Returns:
            评分结果字典
        """
        # 计算各项评分
        process_score = self.score_process(case)
        basic_info_score = self.score_basic_info(case)
        issue_record_score, issue_record_notes = self.score_issue_record(case)
        shipping_detail_score = self.score_shipping_detail(case)
        
        scores = {
            "工单-流程": process_score,
            "工单-基本信息": basic_info_score,
            "工单-问题记录": issue_record_score,
            "工单-发货明细": shipping_detail_score,
        }
        
        # 生成质检记录和问题记录
        quality_record = self.generate_quality_record(case, scores)
        issue_notes = self.generate_issue_notes(case, scores, issue_record_notes)
        
        # 构建输出结果
        result = {
            "关联单号": case.get("案例名称", ""),
            "质检类型": "工单",
            "业务类型": "服务质检",
            "质检记录": "",
            "工单-流程": process_score,
            "工单-基本信息": basic_info_score,
            "工单-问题记录": issue_record_score,
            "工单-发货明细": shipping_detail_score,
            "工单问题记录": issue_notes,
            "负责人": self.get_responsible_person(case),
            "新建时间": case.get("创建时间", "")
        }
        
        return result
    
    def batch_score(self, cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量评分
        
        Args:
            cases: 案例数据列表
            
        Returns:
            评分结果列表
        """
        results = []
        for idx, case in enumerate(cases, 1):
            print(f"[{idx}/{len(cases)}] 正在评分: {case.get('案例名称', '未知')}")
            result = self.score_case(case)
            results.append(result)
        return results


def load_cases_from_json(json_path: str) -> List[Dict[str, Any]]:
    """
    从JSON文件加载案例数据
    
    Args:
        json_path: JSON文件路径
        
    Returns:
        案例数据列表
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 根据实际JSON结构提取数据
    if isinstance(data, dict):
        if "data" in data and "dataList" in data["data"]:
            return data["data"]["dataList"]
        elif "dataList" in data:
            return data["dataList"]
        else:
            # 如果直接是列表
            return data if isinstance(data, list) else []
    elif isinstance(data, list):
        return data
    else:
        return []


def save_results_to_json(results: List[Dict[str, Any]], output_path: str):
    """
    保存评分结果到JSON文件
    
    Args:
        results: 评分结果列表
        output_path: 输出文件路径
    """
    output_data = {
        "data": {
            "dataList": results
        }
    }
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 评分结果已保存到: {output_path}")
    print(f"  共处理 {len(results)} 条记录")


def main():
    """主函数"""
    # 文件路径配置
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "热线受理.json"
    output_file = base_dir / "data" / "qis_scoring_results.json"
    
    print("=" * 60)
    print("工单评分系统")
    print("=" * 60)
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("=" * 60 + "\n")
    
    # 检查输入文件是否存在
    if not input_file.exists():
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        return
    
    # 加载案例数据
    print("正在加载案例数据...")
    cases = load_cases_from_json(str(input_file))
    print(f"✓ 成功加载 {len(cases)} 条案例记录\n")
    
    if not cases:
        print("❌ 未找到案例数据")
        return
    
    # 创建评分器并批量评分
    scorer = CaseScorer()
    print("开始评分...\n")
    try:
        results = scorer.batch_score(cases)
    finally:
        # 确保关闭数据库连接
        scorer.close_db_connection()
    
    # 保存结果
    print("\n" + "=" * 60)
    save_results_to_json(results, str(output_file))
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("评分统计")
    print("=" * 60)
    total_scores = [sum([r.get("工单-流程", 0), r.get("工单-基本信息", 0), 
                        r.get("工单-问题记录", 0), r.get("工单-发货明细", 0)]) 
                    for r in results]
    if total_scores:
        avg_score = sum(total_scores) / len(total_scores)
        max_score = max(total_scores)
        min_score = min(total_scores)
        print(f"平均总分: {avg_score:.2f}")
        print(f"最高分: {max_score}")
        print(f"最低分: {min_score}")
    print("=" * 60)


if __name__ == "__main__":
    main()

