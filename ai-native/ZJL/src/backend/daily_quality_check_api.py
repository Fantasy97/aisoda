"""每日质检自动化流程 Web API 服务"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import io
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# 导入纷享销客查询模块
# 添加tools目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.join(current_dir, 'tools')
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)
from fxiaoke_cases_list_query import query_by_date, convert_to_chinese_fields
from score_cases import CaseScorer, save_results_to_json, DB_CONFIG
from import_scoring_results_to_db import import_json_to_db
from export_scoring_results_to_excel import export_to_excel
from upload_excel_to_oss_and_notify import OSSUploader, FeishuNotifier, DEFAULT_REGION, DEFAULT_BUCKET, DEFAULT_OSS_KEY_PREFIX, FEISHU_WEBHOOK_URL
import pymysql

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "message": "每日质检服务运行正常"
    })


def execute_quality_check_internal(target_date: Optional[datetime] = None, 
                                    export_excel: bool = True, 
                                    skip_duplicates: bool = True) -> Dict[str, Any]:
    """
    执行质检流程的内部函数（不依赖 Flask request）
    
    Args:
        target_date: 目标日期，如果为None则使用昨天
        export_excel: 是否导出Excel，默认True
        skip_duplicates: 是否跳过重复记录，默认True
        
    Returns:
        dict: 执行结果
    """
    try:
        # 解析日期参数
        if target_date is None:
            # 默认使用昨天
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = today_start - timedelta(days=1)
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        logger.info(f"[定时任务] 开始执行每日质检: 日期={date_str}, 导出Excel={export_excel}, 跳过重复={skip_duplicates}")
        
        # 步骤1: 从纷享销客获取数据并导入数据库
        logger.info("[定时任务] 步骤1: 从纷享销客获取数据并导入数据库...")
        try:
            query_results = query_by_date(
                target_date=target_date,
                save_files=True,
                query_hotline=True,
                query_replacement=True,
                import_to_db=True,
                skip_duplicates=skip_duplicates
            )
            
            # 统计获取的数据量
            hotline_count = 0
            replacement_count = 0
            hotline_inserted = 0
            replacement_inserted = 0
            
            if query_results.get("hotline") and query_results["hotline"].get("errorCode") == 0:
                hotline_data = query_results["hotline"].get("data", {})
                hotline_list = hotline_data.get("dataList", [])
                
                hotline_count = len(hotline_list)
                if "hotline_import" in query_results:
                    hotline_inserted, hotline_skipped, hotline_errors = query_results["hotline_import"]
                    logger.info(f"  [定时任务] 热线受理: 查询到 {hotline_count} 条, 导入 {hotline_inserted} 条, 跳过 {hotline_skipped} 条, 错误 {hotline_errors} 条")
            
            if query_results.get("replacement") and query_results["replacement"].get("errorCode") == 0:
                replacement_data = query_results["replacement"].get("data", {})
                replacement_list = replacement_data.get("dataList", [])
                
                replacement_count = len(replacement_list)
                if "replacement_import" in query_results:
                    replacement_inserted, replacement_skipped, replacement_errors = query_results["replacement_import"]
                    logger.info(f"  [定时任务] 替换发货: 查询到 {replacement_count} 条, 导入 {replacement_inserted} 条, 跳过 {replacement_skipped} 条, 错误 {replacement_errors} 条")
            
            total_count = hotline_count + replacement_count
            total_inserted = hotline_inserted + replacement_inserted
            
            logger.info(f"[定时任务] ✓ 步骤1完成: 共查询到 {total_count} 条记录, 成功导入 {total_inserted} 条")
            
            if total_count == 0:
                logger.warning(f"[定时任务] 未查询到 {date_str} 的数据")
                return {
                    "success": False,
                    "error": f"未查询到 {date_str} 的数据",
                    "date": date_str
                }
            
        except Exception as e:
            logger.error(f"[定时任务] 步骤1执行失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"从纷享销客获取数据失败: {str(e)}"
            }
        
        # 步骤2: 从查询结果中提取数据进行评分
        logger.info("[定时任务] 步骤2: 从查询结果中提取数据进行评分...")
        scoring_results = []
        
        try:
            all_cases = []
            
            if query_results.get("hotline") and query_results["hotline"].get("errorCode") == 0:
                hotline_data = query_results["hotline"].get("data", {})
                hotline_list = hotline_data.get("dataList", [])
                logger.info(f"  [定时任务] 处理热线受理数据: {len(hotline_list)} 条")
                
                for item in hotline_list:
                    if "案例名称" in item or "name" not in item:
                        all_cases.append(item)
                    else:
                        case_cn = convert_to_chinese_fields(item, use_grouping=False, translate_values=True)
                        all_cases.append(case_cn)
            
            if query_results.get("replacement") and query_results["replacement"].get("errorCode") == 0:
                replacement_data = query_results["replacement"].get("data", {})
                replacement_list = replacement_data.get("dataList", [])
                logger.info(f"  [定时任务] 处理替换发货数据: {len(replacement_list)} 条")
                
                for item in replacement_list:
                    if "案例名称" in item or "name" not in item:
                        all_cases.append(item)
                    else:
                        case_cn = convert_to_chinese_fields(item, use_grouping=False, translate_values=True)
                        all_cases.append(case_cn)
            
            if not all_cases:
                logger.warning("[定时任务] 没有可评分的数据")
                return {
                    "success": False,
                    "error": "没有可评分的数据",
                    "date": date_str
                }
            
            logger.info(f"  [定时任务] 共收集 {len(all_cases)} 条案例数据，开始评分...")
            
            scorer = CaseScorer()
            scoring_results = scorer.batch_score(all_cases)
            
            logger.info(f"[定时任务] ✓ 步骤2完成: 成功评分 {len(scoring_results)} 条记录")
            
        except Exception as e:
            logger.error(f"[定时任务] 步骤2执行失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"评分失败: {str(e)}"
            }
        
        # 步骤3: 将评分结果导入数据库
        logger.info("[定时任务] 步骤3: 将评分结果导入数据库...")
        try:
            if not scoring_results:
                logger.warning("[定时任务] 没有评分结果需要导入")
            else:
                temp_dir = os.path.join(current_dir, '..', '..', 'data', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                temp_json = os.path.join(temp_dir, f'scoring_results_{date_str}.json')
                
                logger.info(f"  [定时任务] 保存评分结果到临时文件: {temp_json}")
                save_results_to_json(scoring_results, temp_json)
                
                logger.info("  [定时任务] 开始导入数据库...")
                import_json_to_db(temp_json, skip_duplicates=skip_duplicates)
                
                logger.info(f"[定时任务] ✓ 步骤3完成: 成功导入 {len(scoring_results)} 条评分结果")
            
        except Exception as e:
            logger.error(f"[定时任务] 步骤3执行失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"导入评分结果到数据库失败: {str(e)}"
            }
        
        # 步骤4-7: 导出Excel、上传OSS、生成链接、发送飞书
        if export_excel:
            logger.info("[定时任务] 步骤4: 导出Excel文件...")
            try:
                start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                output_dir = os.path.join(current_dir, '..', '..', 'data', 'exports')
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f'质检结果_{date_str}.xlsx')
                
                logger.info(f"  [定时任务] 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"  [定时任务] 输出文件: {output_file}")
                
                excel_file = export_to_excel(
                    start_time=start_time,
                    end_time=end_time,
                    output_file=output_file,
                    quality_check_type='工单'
                )
                
                if excel_file and os.path.exists(excel_file):
                    logger.info(f"[定时任务] ✓ 步骤4完成: Excel文件已生成: {excel_file}")
                    
                    # 步骤5: 上传到OSS
                    logger.info("[定时任务] 步骤5: 上传Excel文件到OSS...")
                    try:
                        uploader = OSSUploader(
                            region=DEFAULT_REGION,
                            bucket=DEFAULT_BUCKET
                        )
                        
                        oss_key = DEFAULT_OSS_KEY_PREFIX + os.path.basename(excel_file)
                        logger.info(f"  [定时任务] OSS Key: {oss_key}")
                        
                        upload_result = uploader.upload_file(excel_file, oss_key)
                        
                        if upload_result["success"]:
                            logger.info(f"[定时任务] ✓ 步骤5完成: 文件已上传到OSS")
                        else:
                            raise Exception("上传失败")
                            
                    except Exception as e:
                        logger.error(f"[定时任务] 步骤5执行失败: {str(e)}", exc_info=True)
                        return {
                            "success": False,
                            "error": f"上传Excel文件到OSS失败: {str(e)}"
                        }
                    
                    # 步骤6: 生成预签名URL
                    logger.info("[定时任务] 步骤6: 生成预签名下载链接...")
                    try:
                        url_result = uploader.generate_presigned_url(oss_key, expires_seconds=3600)
                        
                        if url_result["success"]:
                            download_url = url_result["url"]
                            logger.info(f"[定时任务] ✓ 步骤6完成: 预签名链接已生成")
                        else:
                            raise Exception("生成链接失败")
                            
                    except Exception as e:
                        logger.error(f"[定时任务] 步骤6执行失败: {str(e)}", exc_info=True)
                        return {
                            "success": False,
                            "error": f"生成预签名URL失败: {str(e)}"
                        }
                    
                    # 步骤7: 推送给飞书
                    logger.info("[定时任务] 步骤7: 推送下载链接到飞书...")
                    send_success = False
                    try:
                        notifier = FeishuNotifier(webhook_url=FEISHU_WEBHOOK_URL)
                        
                        title = f"质检结果文件 - {date_str}"
                        description = f"日期: {date_str}\n文件: {os.path.basename(excel_file)}\n链接有效期: {url_result['expiration']}"
                        
                        send_success = notifier.send_url(download_url, title=title, description=description)
                        
                        if send_success:
                            logger.info(f"[定时任务] ✓ 步骤7完成: 链接已推送到飞书")
                        else:
                            logger.warning("[定时任务] 步骤7: 飞书通知发送失败，但文件已成功上传")
                            
                    except Exception as e:
                        logger.error(f"[定时任务] 步骤7执行失败: {str(e)}", exc_info=True)
                        logger.warning("[定时任务] 飞书通知发送失败，但文件已成功上传到OSS")
                        send_success = False
                    
                    logger.info(f"[定时任务] ✓ 所有步骤完成！日期: {date_str}")
                    
                    return {
                        "success": True,
                        "date": date_str,
                        "message": "质检流程执行完成",
                        "excel_file": excel_file,
                        "oss": {
                            "bucket": upload_result["bucket"],
                            "key": upload_result["key"]
                        },
                        "download_url": download_url,
                        "url_expiration": url_result["expiration"],
                        "feishu_notified": send_success
                    }
                else:
                    logger.warning("[定时任务] Excel文件生成失败或文件不存在")
                    return {
                        "success": False,
                        "error": "Excel文件生成失败",
                        "date": date_str
                    }
                    
            except Exception as e:
                logger.error(f"[定时任务] 步骤4执行失败: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"导出Excel文件失败: {str(e)}"
                }
        
        return {
            "success": True,
            "date": date_str,
            "message": "质检流程执行完成（未导出Excel）"
        }
        
    except Exception as e:
        logger.error(f"[定时任务] 执行异常: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }


def scheduled_quality_check():
    """定时任务：每天9点执行质检流程"""
    logger.info("=" * 80)
    logger.info("[定时任务] 开始执行每日质检任务（每天9点）")
    logger.info("=" * 80)
    
    try:
        result = execute_quality_check_internal(
            target_date=None,  # 使用默认（昨天）
            export_excel=True,
            skip_duplicates=True
        )
        
        if result.get("success"):
            logger.info(f"[定时任务] ✓ 任务执行成功: {result.get('message', '')}")
        else:
            logger.error(f"[定时任务] ✗ 任务执行失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"[定时任务] ✗ 任务执行异常: {str(e)}", exc_info=True)
    
    logger.info("=" * 80)
    logger.info("[定时任务] 每日质检任务执行完成")
    logger.info("=" * 80)


@app.route('/api/daily-quality-check', methods=['POST'])
def daily_quality_check():
    """
    执行每日质检流程并返回Excel文件
    
    请求体:
    {
        "date": "2025-01-15",  // 可选，格式: YYYY-MM-DD，默认昨天
        "export_excel": true,  // 可选，是否导出Excel，默认true
        "skip_duplicates": true  // 可选，是否跳过重复记录，默认true
    }
    
    响应:
    - 成功: 返回Excel文件下载
    - 失败: 返回JSON错误信息
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        
        # 解析日期参数
        target_date = None
        if 'date' in data and data['date']:
            try:
                target_date = datetime.strptime(data['date'], "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "日期格式错误，应为 YYYY-MM-DD"
                }), 400
        else:
            # 默认使用昨天
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = today_start - timedelta(days=1)
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        # 获取其他参数
        export_excel = data.get('export_excel', True)
        skip_duplicates = data.get('skip_duplicates', True)
        
        logger.info(f"收到每日质检请求: 日期={date_str}, 导出Excel={export_excel}, 跳过重复={skip_duplicates}")
        
        # 步骤1: 从纷享销客获取数据并导入数据库
        logger.info("步骤1: 从纷享销客获取数据并导入数据库...")
        try:
            query_results = query_by_date(
                target_date=target_date,
                save_files=True,  # 不保存JSON文件
                query_hotline=True,
                query_replacement=True,
                import_to_db=True,  # 导入到数据库
                skip_duplicates=skip_duplicates
            )
            
            # 统计获取的数据量
            hotline_count = 0
            replacement_count = 0
            hotline_inserted = 0
            replacement_inserted = 0
            
            if query_results.get("hotline") and query_results["hotline"].get("errorCode") == 0:
                hotline_data = query_results["hotline"].get("data", {})
                hotline_list = hotline_data.get("dataList", [])
                
                hotline_count = len(hotline_list)
                if "hotline_import" in query_results:
                    hotline_inserted, hotline_skipped, hotline_errors = query_results["hotline_import"]
                    logger.info(f"  热线受理: 查询到 {hotline_count} 条, 导入 {hotline_inserted} 条, 跳过 {hotline_skipped} 条, 错误 {hotline_errors} 条")
            
            if query_results.get("replacement") and query_results["replacement"].get("errorCode") == 0:
                replacement_data = query_results["replacement"].get("data", {})
                replacement_list = replacement_data.get("dataList", [])
                
                replacement_count = len(replacement_list)
                if "replacement_import" in query_results:
                    replacement_inserted, replacement_skipped, replacement_errors = query_results["replacement_import"]
                    logger.info(f"  替换发货: 查询到 {replacement_count} 条, 导入 {replacement_inserted} 条, 跳过 {replacement_skipped} 条, 错误 {replacement_errors} 条")
            
            total_count = hotline_count + replacement_count
            total_inserted = hotline_inserted + replacement_inserted
            
            logger.info(f"✓ 步骤1完成: 共查询到 {total_count} 条记录, 成功导入 {total_inserted} 条")
            
            if total_count == 0:
                logger.warning(f"未查询到 {date_str} 的数据")
                return jsonify({
                    "success": False,
                    "error": f"未查询到 {date_str} 的数据",
                    "date": date_str
                }), 404
            
        except Exception as e:
            logger.error(f"步骤1执行失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"从纷享销客获取数据失败: {str(e)}"
            }), 500
        
        # 步骤2: 从查询结果中提取数据进行评分
        logger.info("步骤2: 从查询结果中提取数据进行评分...")
        scoring_results = []  # 初始化评分结果列表
        
        try:
            # 收集所有案例数据（热线受理 + 替换发货）
            all_cases = []
            
            # 处理热线受理数据
            if query_results.get("hotline") and query_results["hotline"].get("errorCode") == 0:
                hotline_data = query_results["hotline"].get("data", {})
                hotline_list = hotline_data.get("dataList", [])
                logger.info(f"  处理热线受理数据: {len(hotline_list)} 条")
                
                # 转换为中文字段格式
                for item in hotline_list:
                    # 检查是否已经是中文字段格式
                    if "案例名称" in item or "name" not in item:
                        # 已经是中文字段，直接使用
                        all_cases.append(item)
                    else:
                        # 转换为中文字段
                        case_cn = convert_to_chinese_fields(item, use_grouping=False, translate_values=True)
                        all_cases.append(case_cn)
            
            # 处理替换发货数据
            if query_results.get("replacement") and query_results["replacement"].get("errorCode") == 0:
                replacement_data = query_results["replacement"].get("data", {})
                replacement_list = replacement_data.get("dataList", [])
                logger.info(f"  处理替换发货数据: {len(replacement_list)} 条")
                
                # 转换为中文字段格式
                for item in replacement_list:
                    # 检查是否已经是中文字段格式
                    if "案例名称" in item or "name" not in item:
                        # 已经是中文字段，直接使用
                        all_cases.append(item)
                    else:
                        # 转换为中文字段
                        case_cn = convert_to_chinese_fields(item, use_grouping=False, translate_values=True)
                        all_cases.append(case_cn)
            
            if not all_cases:
                logger.warning("没有可评分的数据")
                return jsonify({
                    "success": False,
                    "error": "没有可评分的数据",
                    "date": date_str
                }), 404
            
            logger.info(f"  共收集 {len(all_cases)} 条案例数据，开始评分...")
            
            # 创建评分器并批量评分
            scorer = CaseScorer()
            scoring_results = scorer.batch_score(all_cases)
            
            logger.info(f"✓ 步骤2完成: 成功评分 {len(scoring_results)} 条记录")
            
        except Exception as e:
            logger.error(f"步骤2执行失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"评分失败: {str(e)}"
            }), 500
        
        # 步骤3: 将评分结果导入数据库
        logger.info("步骤3: 将评分结果导入数据库...")
        try:
            if not scoring_results:
                logger.warning("没有评分结果需要导入")
            else:
                # 保存为临时JSON文件
                temp_dir = os.path.join(current_dir, '..', '..', 'data', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                temp_json = os.path.join(temp_dir, f'scoring_results_{date_str}.json')
                
                logger.info(f"  保存评分结果到临时文件: {temp_json}")
                save_results_to_json(scoring_results, temp_json)
                
                # 导入数据库
                logger.info("  开始导入数据库...")
                import_json_to_db(temp_json, skip_duplicates=skip_duplicates)
                
                logger.info(f"✓ 步骤3完成: 成功导入 {len(scoring_results)} 条评分结果")
                
                # 可选：删除临时文件（如果需要可以取消注释）
                # try:
                #     os.remove(temp_json)
                #     logger.info(f"  已删除临时文件: {temp_json}")
                # except Exception as e:
                #     logger.warning(f"  删除临时文件失败: {e}")
            
        except Exception as e:
            logger.error(f"步骤3执行失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"导入评分结果到数据库失败: {str(e)}"
            }), 500
        
        # 步骤4: 导出Excel文件
        if export_excel:
            logger.info("步骤4: 导出Excel文件...")
            try:
                # 计算时间范围（该日期的 00:00:00 到 23:59:59）
                start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # 生成输出文件路径
                output_dir = os.path.join(current_dir, '..', '..', 'data', 'exports')
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f'质检结果_{date_str}.xlsx')
                
                logger.info(f"  时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"  输出文件: {output_file}")
                
                # 导出Excel文件
                excel_file = export_to_excel(
                    start_time=start_time,
                    end_time=end_time,
                    output_file=output_file,
                    quality_check_type='工单'  # 只导出工单类型的评分结果
                )
                
                if excel_file and os.path.exists(excel_file):
                    logger.info(f"✓ 步骤4完成: Excel文件已生成: {excel_file}")
                    
                    # 步骤5: 上传导出Excel文件到OSS
                    logger.info("步骤5: 上传Excel文件到OSS...")
                    try:
                        # 初始化OSS上传器（使用环境变量中的凭证）
                        uploader = OSSUploader(
                            region=DEFAULT_REGION,
                            bucket=DEFAULT_BUCKET
                        )
                        
                        # 生成OSS key（使用默认前缀 + 文件名）
                        oss_key = DEFAULT_OSS_KEY_PREFIX + os.path.basename(excel_file)
                        logger.info(f"  OSS Key: {oss_key}")
                        
                        # 上传文件
                        upload_result = uploader.upload_file(excel_file, oss_key)
                        
                        if upload_result["success"]:
                            logger.info(f"✓ 步骤5完成: 文件已上传到OSS")
                            logger.info(f"  Bucket: {upload_result['bucket']}")
                            logger.info(f"  Key: {upload_result['key']}")
                        else:
                            raise Exception("上传失败")
                            
                    except Exception as e:
                        logger.error(f"步骤5执行失败: {str(e)}", exc_info=True)
                        return jsonify({
                            "success": False,
                            "error": f"上传Excel文件到OSS失败: {str(e)}"
                        }), 500
                    
                    # 步骤6: 生成预签名URL
                    logger.info("步骤6: 生成预签名下载链接...")
                    try:
                        # 生成预签名链接（有效期1小时）
                        url_result = uploader.generate_presigned_url(oss_key, expires_seconds=3600)
                        
                        if url_result["success"]:
                            download_url = url_result["url"]
                            logger.info(f"✓ 步骤6完成: 预签名链接已生成")
                            logger.info(f"  链接有效期至: {url_result['expiration']}")
                        else:
                            raise Exception("生成链接失败")
                            
                    except Exception as e:
                        logger.error(f"步骤6执行失败: {str(e)}", exc_info=True)
                        return jsonify({
                            "success": False,
                            "error": f"生成预签名URL失败: {str(e)}"
                        }), 500
                    
                    # 步骤7: 推送给飞书
                    logger.info("步骤7: 推送下载链接到飞书...")
                    send_success = False  # 初始化变量
                    try:
                        # 初始化飞书通知器
                        notifier = FeishuNotifier(webhook_url=FEISHU_WEBHOOK_URL)
                        
                        # 构建消息标题和描述
                        title = f"质检结果文件 - {date_str}"
                        description = f"日期: {date_str}\n文件: {os.path.basename(excel_file)}\n链接有效期: {url_result['expiration']}"
                        
                        # 发送到飞书
                        send_success = notifier.send_url(download_url, title=title, description=description)
                        
                        if send_success:
                            logger.info(f"✓ 步骤7完成: 链接已推送到飞书")
                        else:
                            logger.warning("步骤7: 飞书通知发送失败，但文件已成功上传")
                            
                    except Exception as e:
                        logger.error(f"步骤7执行失败: {str(e)}", exc_info=True)
                        # 飞书通知失败不影响整体流程，只记录警告
                        logger.warning("飞书通知发送失败，但文件已成功上传到OSS")
                        send_success = False
                    
                    # 返回成功信息，包含下载链接
                    return jsonify({
                        "success": True,
                        "date": date_str,
                        "message": "质检流程执行完成",
                        "excel_file": excel_file,
                        "oss": {
                            "bucket": upload_result["bucket"],
                            "key": upload_result["key"]
                        },
                        "download_url": download_url,
                        "url_expiration": url_result["expiration"],
                        "feishu_notified": send_success
                    })
                    
                else:
                    logger.warning("Excel文件生成失败或文件不存在")
                    return jsonify({
                        "success": False,
                        "error": "Excel文件生成失败",
                        "date": date_str
                    }), 500
                    
            except Exception as e:
                logger.error(f"步骤4执行失败: {str(e)}", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": f"导出Excel文件失败: {str(e)}"
                }), 500
        
        return jsonify({
            "success": True,
            "date": date_str,
            "message": "质检流程执行完成（未导出Excel）"
        })
    
    except Exception as e:
        logger.error(f"每日质检异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.route('/api/daily-quality-check/download', methods=['POST'])
def download_excel():
    """
    下载指定日期的质检结果Excel文件
    
    请求体:
    {
        "date": "2025-01-15"  // 可选，格式: YYYY-MM-DD，默认昨天
    }
    
    响应:
    - 成功: 返回Excel文件下载
    - 失败: 返回JSON错误信息
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        
        # 解析日期参数
        target_date = None
        if 'date' in data and data['date']:
            try:
                target_date = datetime.strptime(data['date'], "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "日期格式错误，应为 YYYY-MM-DD"
                }), 400
        else:
            # 默认使用昨天
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = today_start - timedelta(days=1)
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        logger.info(f"收到Excel下载请求: 日期={date_str}")
        
        # TODO: 从数据库查询并生成Excel文件
        # start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        # excel_file = export_to_excel(
        #     start_time=start_time,
        #     end_time=end_time,
        #     quality_check_type='工单'
        # )
        
        # 临时返回示例（实际需要替换为真实文件）
        return jsonify({
            "success": False,
            "error": "Excel下载功能待实现",
            "message": "请完善 export_to_excel 函数调用和文件返回逻辑"
        }), 501  # 501 Not Implemented
        
        # 实际实现示例（需要取消注释并完善）:
        # if excel_file and os.path.exists(excel_file):
        #     return send_file(
        #         excel_file,
        #         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        #         as_attachment=True,
        #         download_name=f'质检结果_{date_str}.xlsx'
        #     )
        # else:
        #     return jsonify({
        #         "success": False,
        #         "error": "Excel文件不存在"
        #     }), 404
    
    except Exception as e:
        logger.error(f"Excel下载异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


def query_case_from_db(case_number: str) -> Optional[Dict[str, Any]]:
    """
    从数据库查询工单数据
    
    Args:
        case_number: 工单号（案例名称）
        
    Returns:
        工单数据字典（中文字段格式），如果未找到则返回None
    """
    connection = None
    cursor = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询数据库中的工单数据
        sql = """
            SELECT * FROM `qis_cases_info` 
            WHERE `name` = %s
            LIMIT 1
        """
        cursor.execute(sql, (case_number,))
        db_record = cursor.fetchone()
        
        if not db_record:
            return None
        
        # 将数据库字段转换为API格式（使用owner_id而不是owner），然后使用convert_to_chinese_fields转换
        # 数据库字段到API字段的映射
        db_to_api_mapping = {
            'name': 'name',
            'create_time': 'create_time',
            'owner': 'owner_id',  # 数据库使用owner，API使用owner_id
            'record_type': 'record_type',
            'field_v24BD__c': 'field_v24BD__c',
            'field_Utj19__c': 'field_Utj19__c',
            'field_0uAwt__c': 'field_0uAwt__c',
            'field_toFhx__c': 'field_toFhx__c',
            'field_iywKQ__c': 'field_iywKQ__c',
            'field_93r62__c': 'field_93r62__c',
            'field_o1oCe__c': 'field_o1oCe__c',
            'field_3ff0E__c': 'field_3ff0E__c',
            'field_812NN__c': 'field_812NN__c',
            'field_Mc0p7__c': 'field_Mc0p7__c',
            'field_glsb__c': 'field_glsb__c',
            'field_TWcZV__c': 'field_TWcZV__c',  # 备用序号
            'account_id': 'account_id',
            'field_sZHpO__c': 'field_sZHpO__c',
            'field_glcp__c': 'field_glcp__c',
            'field_FGMjJ__c': 'field_FGMjJ__c',
            'field_h017i__c': 'field_h017i__c',
            'field_1H53l__c': 'field_1H53l__c',
            'field_3oyKy__c': 'field_3oyKy__c'
        }
        
        # 转换为API格式
        api_record = {}
        for db_field, api_field in db_to_api_mapping.items():
            value = db_record.get(db_field)
            # 处理datetime对象，转换为字符串
            if isinstance(value, datetime):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            api_record[api_field] = value
        
        # 使用convert_to_chinese_fields转换为中文字段格式
        case_cn = convert_to_chinese_fields(api_record, use_grouping=False, translate_values=True)
        
        return case_cn
        
    except Exception as e:
        logger.error(f"从数据库查询工单失败: {str(e)}", exc_info=True)
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route('/api/score-case', methods=['POST'])
def score_case_by_number():
    """
    根据工单号从数据库读取数据并进行评分
    
    请求体:
    {
        "case_number": "CN2024011708976"  // 必填，工单号（案例名称）
    }
    
    响应:
    {
        "success": true,
        "case_number": "CN2024011708976",
        "case_info": {
            // 原始工单信息（中文字段格式）
        },
        "result": {
            "关联单号": "...",
            "质检类型": "工单",
            "业务类型": "服务质检",
            "工单-流程": 30,
            "工单-基本信息": 20,
            "工单-问题记录": 35,
            "工单-发货明细": 15,
            "工单问题记录": "...",
            "负责人": "...",
            "新建时间": "..."
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        case_number = data.get('case_number', '').strip()
        
        if not case_number:
            return jsonify({
                "success": False,
                "error": "工单号不能为空，请提供 case_number 参数"
            }), 400
        
        logger.info(f"收到工单评分请求: 工单号={case_number}")
        
        # 从数据库查询工单数据
        case_data = query_case_from_db(case_number)
        
        if not case_data:
            logger.warning(f"未找到工单: {case_number}")
            return jsonify({
                "success": False,
                "error": f"未找到工单号 {case_number} 的数据",
                "case_number": case_number
            }), 404
        
        # 进行评分
        try:
            scorer = CaseScorer()
            scoring_result = scorer.score_case(case_data)
            scorer.close_db_connection()  # 关闭数据库连接
            
            logger.info(f"✓ 工单评分完成: {case_number}")
            
            return jsonify({
                "success": True,
                "case_number": case_number,
                "case_info": case_data,  # 原始工单信息（中文字段格式）
                "result": scoring_result
            })
            
        except Exception as e:
            logger.error(f"评分失败: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"评分失败: {str(e)}",
                "case_number": case_number
            }), 500
        
    except Exception as e:
        logger.error(f"工单评分异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.route('/api/daily-quality-check/status', methods=['POST'])
def check_status():
    """
    查询指定日期的质检执行状态
    
    请求体:
    {
        "date": "2025-01-15"  // 可选，格式: YYYY-MM-DD，默认昨天
    }
    
    响应:
    {
        "success": true,
        "date": "2025-01-15",
        "status": "completed",  // completed, processing, failed, not_found
        "data_count": 100,
        "scoring_count": 95,
        "excel_file": "path/to/file.xlsx"  // 可选
    }
    """
    try:
        # 获取请求参数
        data = request.get_json() or {}
        
        # 解析日期参数
        target_date = None
        if 'date' in data and data['date']:
            try:
                target_date = datetime.strptime(data['date'], "%Y-%m-%d")
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "日期格式错误，应为 YYYY-MM-DD"
                }), 400
        else:
            # 默认使用昨天
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = today_start - timedelta(days=1)
        
        date_str = target_date.strftime("%Y-%m-%d")
        
        logger.info(f"收到状态查询请求: 日期={date_str}")
        
        # TODO: 查询数据库获取执行状态
        # 可以从数据库查询：
        # 1. 该日期的案例数据数量
        # 2. 该日期的评分结果数量
        # 3. Excel文件是否存在
        
        return jsonify({
            "success": True,
            "date": date_str,
            "status": "not_implemented",  # 待实现
            "message": "状态查询功能待实现"
        })
    
    except Exception as e:
        logger.error(f"状态查询异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║              每日质检自动化流程 Web API 服务                    ║
╚══════════════════════════════════════════════════════════════╝

API 接口:
  GET  /health                              - 健康检查
  POST /api/daily-quality-check             - 执行质检流程并返回Excel
  POST /api/daily-quality-check/download    - 下载Excel文件
  POST /api/daily-quality-check/status      - 查询执行状态
  POST /api/score-case                      - 根据工单号从数据库读取并评分

请求示例:
  POST /api/daily-quality-check
  {
    "date": "2025-01-15",
    "export_excel": true,
    "skip_duplicates": true
  }
  
  POST /api/score-case
  {
    "case_number": "CN2024011708976"
  }

启动信息:
  • 服务地址: http://localhost:5009
  • 跨域支持: 已启用
  • 日志级别: INFO
  • 定时任务: 每天 09:00 (北京时间) 自动执行质检流程

注意:
  • 所有函数调用标记为 TODO，需要自行完善
  • 日期参数可选，默认使用昨天
  • Excel文件下载需要完善文件返回逻辑

""")
    
    try:
        # 设置时区为北京时间（Asia/Shanghai）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        # 创建并启动定时任务调度器，设置时区
        scheduler = BackgroundScheduler(timezone=beijing_tz)
        
        # 添加定时任务：每天9点执行（北京时间）
        scheduler.add_job(
            func=scheduled_quality_check,
            trigger=CronTrigger(hour=9, minute=0, timezone=beijing_tz),  # 每天9点（北京时间）
            id='daily_quality_check',
            name='每日质检任务',
            replace_existing=True
        )
        
        # 启动调度器
        scheduler.start()
        logger.info("✓ 定时任务调度器已启动")
        logger.info("  - 任务名称: 每日质检任务")
        logger.info("  - 执行时间: 每天 09:00 (北京时间)")
        logger.info("  - 时区: Asia/Shanghai (UTC+8)")
        logger.info("  - 任务ID: daily_quality_check")
        
        # 显示下次执行时间
        job = scheduler.get_job('daily_quality_check')
        if job:
            next_run = job.next_run_time
            if next_run:
                next_run_beijing = next_run.astimezone(beijing_tz)
                logger.info(f"  - 下次执行时间: {next_run_beijing.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        print("\n✓ 定时任务已启动: 每天 09:00 (北京时间) 自动执行质检流程\n")
        
        # 启动Flask服务
        app.run(
            host='0.0.0.0',
            port=5009,  # 使用不同端口避免与app.py冲突
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}", exc_info=True)
        print(f"\n❌ 服务启动失败: {e}")
        sys.exit(1)
    finally:
        # 关闭调度器
        if 'scheduler' in locals() and scheduler.running:
            scheduler.shutdown()
            logger.info("定时任务调度器已关闭")

