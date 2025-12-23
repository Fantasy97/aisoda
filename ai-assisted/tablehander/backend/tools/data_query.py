import json
import os
from typing import Dict, Any, List, Tuple
import difflib
import re


class DataQueryHandler:
    """数据查询处理器，用于通过部分key查询value"""
    
    def __init__(self, data_file_path: str = None):
        """
        初始化数据查询处理器
        
        Args:
            data_file_path: JSON数据文件路径，默认为相对路径
        """
        if data_file_path is None:
            # 默认数据文件路径 - 使用绝对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 从backend/tools目录向上两级到达项目根目录，然后进入data目录
            project_root = os.path.dirname(os.path.dirname(current_dir))
            self.data_file_path = os.path.join(project_root, 'data', 'example_data.json')
        else:
            self.data_file_path = data_file_path
        
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """加载JSON数据文件"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"数据文件未找到: {self.data_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"JSON文件格式错误: {self.data_file_path}")
    
    def _calculate_similarity(self, search_key: str, target_key: str, case_sensitive: bool = False) -> Tuple[float, str]:
        """
        计算两个字符串的相似度
        
        Args:
            search_key: 搜索关键词
            target_key: 目标键名
            case_sensitive: 是否区分大小写
            
        Returns:
            (相似度分数, 匹配类型)
        """
        if not case_sensitive:
            search_key = search_key.lower()
            target_key = target_key.lower()
        
        # 1. 完全匹配
        if search_key == target_key:
            return 1.0, "完全匹配"
        
        # 2. 包含匹配
        if search_key in target_key:
            # 计算包含匹配的相似度（基于长度比例）
            # 对于短关键词，给予更高的基础分数，避免因长度比例过小而被过滤
            length_ratio = len(search_key) / len(target_key)
            # 如果关键词长度<=3，给予额外的权重提升
            if len(search_key) <= 3:
                # 基础分数0.5 + 长度比例的50%，确保短词也能被搜到
                similarity = 0.5 + (length_ratio * 0.5)
            else:
                # 长关键词使用原有逻辑，但提升基础分数
                similarity = 0.4 + (length_ratio * 0.6)
            return min(similarity, 0.95), "包含匹配"  # 最高不超过0.95，保留完全匹配的优势
        
        # 3. 序列匹配器相似度
        seq_similarity = difflib.SequenceMatcher(None, search_key, target_key).ratio()
        
        # 4. 编辑距离相似度
        edit_distance = self._levenshtein_distance(search_key, target_key)
        max_len = max(len(search_key), len(target_key))
        edit_similarity = 1 - (edit_distance / max_len) if max_len > 0 else 0
        
        # 5. 单词级别匹配
        search_words = set(re.findall(r'\w+', search_key))
        target_words = set(re.findall(r'\w+', target_key))
        if search_words and target_words:
            word_similarity = len(search_words & target_words) / len(search_words | target_words)
        else:
            word_similarity = 0
        
        # 综合相似度计算（加权平均）
        final_similarity = (seq_similarity * 0.4 + edit_similarity * 0.4 + word_similarity * 0.2)
        
        if final_similarity >= 0.6:
            return final_similarity, "高相似度匹配"
        elif final_similarity >= 0.3:
            return final_similarity, "中等相似度匹配"
        else:
            return final_similarity, "低相似度匹配"
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def query_by_partial_key(self, partial_key: str, case_sensitive: bool = False, include_context: bool = False, 
                           similarity_threshold: float = 0.15, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        通过部分key智能查询（支持相似度匹配）
        
        Args:
            partial_key: 部分键名
            case_sensitive: 是否区分大小写
            include_context: 是否包含上下文推荐
            similarity_threshold: 相似度阈值（0-1之间），默认0.15
            max_results: 最大返回结果数
            
        Returns:
            包含查询结果的列表，按相似度排序
        """
        results = []
        matched_keys = set()
        search_key = partial_key if case_sensitive else partial_key.lower()
        data_source = os.path.basename(self.data_file_path)
        
        # 获取所有键的列表
        all_keys = list(self.data.keys())
        
        # 计算所有键的相似度
        similarity_scores = []
        for key in all_keys:
            similarity, match_type = self._calculate_similarity(search_key, key, case_sensitive)
            if similarity >= similarity_threshold:
                similarity_scores.append((key, similarity, match_type))
        
        # 按相似度排序（降序）
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 限制结果数量
        similarity_scores = similarity_scores[:max_results]
        
        # 构建结果
        for key, similarity, match_type in similarity_scores:
            if key not in matched_keys:
                result_item = {
                    "key": key,
                    "value": self.data[key],
                    "数据源": data_source,
                    "查询方式": match_type,
                    "相似度": round(similarity, 3),
                    "匹配度": f"{round(similarity * 100, 1)}%"
                }
                results.append(result_item)
                matched_keys.add(key)
        
        # 上下文推荐（仅对高相似度匹配）
        if include_context:
            context_results = []
            for key, similarity, match_type in similarity_scores:
                if similarity >= 0.1:  # 只对高相似度的结果提供上下文
                    try:
                        current_index = all_keys.index(key)
                        # 获取前后各一条记录
                        for offset in [-1, 1]:
                            context_index = current_index + offset
                            if 0 <= context_index < len(all_keys):
                                context_key = all_keys[context_index]
                                if context_key not in matched_keys:
                                    context_item = {
                                        "key": context_key,
                                        "value": self.data[context_key],
                                        "数据源": data_source,
                                        "查询方式": "上下文推荐",
                                        "相似度": 0.0,
                                        "匹配度": "上下文",
                                        "关联键": key
                                    }
                                    context_results.append(context_item)
                                    matched_keys.add(context_key)
                    except ValueError:
                        continue
            
            # 将上下文结果添加到主结果后面
            results.extend(context_results)
        
        return results

    def get_query_results_json(self, partial_key: str, case_sensitive: bool = False, include_context: bool = False,
                             similarity_threshold: float = 0.15, max_results: int = 20) -> str:
        """
        返回JSON格式的查询结果
        
        Args:
            partial_key: 部分键名
            case_sensitive: 是否区分大小写
            include_context: 是否包含上下文推荐
            similarity_threshold: 相似度阈值
            max_results: 最大返回结果数
            
        Returns:
            JSON格式的查询结果字符串
        """
        results = self.query_by_partial_key(partial_key, case_sensitive, include_context, 
                                          similarity_threshold, max_results)
        return json.dumps(results, ensure_ascii=False, indent=2)

    def get_history_files_info(self) -> List[Dict[str, Any]]:
        """
        获取history目录下所有JSON文件的信息
        
        Returns:
            包含文件名和记录数量的列表
        """
        # 使用绝对路径构建history目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        history_dir = os.path.join(project_root, 'data', 'history')
        files_info = []
        
        if not os.path.exists(history_dir):
            return files_info
        
        try:
            for filename in os.listdir(history_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(history_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            data = json.load(file)
                            record_count = len(data["document_structure"]) if isinstance(data, dict) else 0
                            
                            file_info = {
                                "文件名": filename,
                                "记录数量": record_count,
                                "文件路径": file_path
                            }
                            files_info.append(file_info)
                    except (json.JSONDecodeError, Exception) as e:
                        # 如果文件读取失败，仍然记录文件名但标记错误
                        file_info = {
                            "文件名": filename,
                            "记录数量": 0,
                            "文件路径": file_path,
                            "错误": str(e)
                        }
                        files_info.append(file_info)
        except Exception as e:
            print(f"读取history目录失败: {e}")
        
        return files_info

    def get_history_files_json(self) -> str:
        """
        返回JSON格式的history文件信息
        
        Returns:
            JSON格式的文件信息字符串
        """
        files_info = self.get_history_files_info()
        return json.dumps(files_info, ensure_ascii=False, indent=2)

    def get_file_by_name(self, filename: str) -> Dict[str, Any]:
        """
        根据文件名获取data/history目录下的完整JSON内容
        
        Args:
            filename: 文件名（支持部分匹配）
            
        Returns:
            包含文件内容和元信息的字典
        """
        # 使用绝对路径构建history目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        history_dir = os.path.join(project_root, 'data', 'history')
        
        if not os.path.exists(history_dir):
            return {
                "success": False,
                "message": "history目录不存在",
                "data": None
            }
        
        # 查找匹配的文件
        matched_files = []
        try:
            for file in os.listdir(history_dir):
                if file.endswith('.json'):
                    # 支持部分匹配和完整匹配
                    if filename.lower() in file.lower() or file.lower() == filename.lower():
                        matched_files.append(file)
        except Exception as e:
            return {
                "success": False,
                "message": f"读取history目录失败: {str(e)}",
                "data": None
            }
        
        if not matched_files:
            return {
                "success": False,
                "message": f"未找到匹配的文件: {filename}",
                "data": None
            }
        
        if len(matched_files) > 1:
            return {
                "success": False,
                "message": f"找到多个匹配的文件: {', '.join(matched_files)}，请使用更精确的文件名",
                "data": None,
                "matched_files": matched_files
            }
        
        # 读取文件内容
        target_file = matched_files[0]
        file_path = os.path.join(history_dir, target_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = json.load(file)
                
                return {
                    "success": True,
                    "message": f"成功读取文件: {target_file}",
                    "file_info": {
                        "文件名": target_file,
                        "相对路径": os.path.join('data', 'history', target_file),
                        "绝对路径": file_path,
                        "记录数量": len(content.get("document_structure", [])) if isinstance(content, dict) else len(content) if isinstance(content, list) else 1
                    },
                    "data": content
                }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"JSON格式错误: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"读取文件失败: {str(e)}",
                "data": None
            }

    def update_example_data(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新example_data.json文件
        
        Args:
            update_data: 要更新的数据，格式为 {key: value, ...}
            
        Returns:
            包含更新结果的字典
        """
        try:
            # 1. 备份当前数据
            original_data = self.data.copy()
            
            # 2. 统计更新信息
            updated_keys = []
            added_keys = []
            
            # 3. 更新数据
            for key, value in update_data.items():
                if key in self.data:
                    # 键存在，更新数据
                    if self.data[key] != value:
                        self.data[key] = value
                        updated_keys.append(key)
                else:
                    # 键不存在，添加记录
                    self.data[key] = value
                    added_keys.append(key)
            
            # 4. 删除所有value为空的记录
            empty_keys = []
            keys_to_remove = []
            
            for key, value in list(self.data.items()):
                # 检查value是否为空（None、空字符串、空列表、空字典等）
                if value is None or value == "" or value == [] or value == {} or value == "@":
                    keys_to_remove.append(key)
                    empty_keys.append(key)
            
            # 删除空值记录
            for key in keys_to_remove:
                del self.data[key]
            
            # 5. 保存到文件
            with open(self.data_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.data, file, ensure_ascii=False, indent=2)
            
            # 6. 返回更新结果
            return {
                "success": True,
                "message": "数据更新成功",
                "statistics": {
                    "更新的键": len(updated_keys),
                    "新增的键": len(added_keys),
                    "删除的空值键": len(empty_keys),
                    "总记录数": len(self.data)
                },
                "details": {
                    "updated_keys": updated_keys,
                    "added_keys": added_keys,
                    "removed_empty_keys": empty_keys
                },
                "file_path": self.data_file_path
            }
            
        except Exception as e:
            # 如果出错，恢复原始数据
            self.data = original_data
            return {
                "success": False,
                "message": f"更新失败: {str(e)}",
                "statistics": {
                    "更新的键": 0,
                    "新增的键": 0,
                    "删除的空值键": 0,
                    "总记录数": len(self.data)
                },
                "details": {
                    "updated_keys": [],
                    "added_keys": [],
                    "removed_empty_keys": []
                },
                "file_path": self.data_file_path
            }

    def update_example_data_json(self, update_data: Dict[str, Any]) -> str:
        """
        返回JSON格式的更新结果
        
        Args:
            update_data: 要更新的数据
            
        Returns:
            JSON格式的更新结果字符串
        """
        result = self.update_example_data(update_data)
        return json.dumps(result, ensure_ascii=False, indent=2)


def cli_query(query_handler, search_term, include_context=False, similarity_threshold=0.15):
    """执行查询并显示结果"""
    print(f"🔍 搜索关键词: '{search_term}'")
    print(f"🎯 相似度阈值: {similarity_threshold}")
    if include_context:
        print("📋 包含上下文推荐")
    print("-" * 50)
    
    results = query_handler.query_by_partial_key(search_term, include_context=include_context, 
                                               similarity_threshold=similarity_threshold)
    
    if results:
        # 分别统计不同类型的匹配数量
        match_types = {}
        for result in results:
            match_type = result['查询方式']
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        print(f"✅ 找到 {len(results)} 条结果:")
        for match_type, count in match_types.items():
            print(f"   • {match_type}: {count} 条")
        print()
        
        for i, result in enumerate(results, 1):
            # 根据查询方式使用不同的图标
            icons = {
                "完全匹配": "🎯",
                "包含匹配": "🔍", 
                "高相似度匹配": "⭐",
                "中等相似度匹配": "🔸",
                "低相似度匹配": "🔹",
                "上下文推荐": "💡"
            }
            icon = icons.get(result['查询方式'], "📄")
            
            print(f"{i:2d}. {icon} 字段名: {result['key']}")
            print(f"    值: {result['value']}")
            print(f"    数据源: {result['数据源']}")
            print(f"    查询方式: {result['查询方式']}")
            
            if 'matchScore' in result and result['查询方式'] != '上下文推荐':
                print(f"    匹配度: {result['匹配度']}")
            
            if 'relatedKey' in result:
                print(f"    关联键: {result['关联键']}")
            
            print()
    else:
        print("❌ 未找到匹配的数据")
        print(f"💡 提示: 尝试降低相似度阈值（当前: {similarity_threshold}）或使用更通用的关键词")


def cli_show_history(query_handler):
    """显示history目录下的文件信息"""
    print("📁 History目录文件信息")
    print("-" * 50)
    
    files_info = query_handler.get_history_files_info()
    
    if files_info:
        print(f"✅ 找到 {len(files_info)} 个JSON文件:")
        print()
        total_records = 0
        
        for i, file_info in enumerate(files_info, 1):
            print(f"{i:2d}. 📄 文件名: {file_info['文件名']}")
            print(f"    📊 记录数量: {file_info['记录数量']}")
            if "错误" in file_info:
                print(f"    ❌ 错误: {file_info['错误']}")
            else:
                total_records += file_info['记录数量']
            print()
        
        if total_records > 0:
            print(f"📈 总记录数: {total_records}")
    else:
        print("❌ 未找到JSON文件或history目录不存在")





def main():
    """主函数 - 支持命令行参数"""
    import sys
    
    if len(sys.argv) > 1:
        # 检查参数
        args = sys.argv[1:]
        json_output = False
        include_context = False
        similarity_threshold = 0.15
        max_results = 20
        
        # 解析参数
        i = 0
        while i < len(args):
            if args[i] == "--json":
                json_output = True
                args.pop(i)
            elif args[i] == "--context":
                include_context = True
                args.pop(i)
            elif args[i] == "--similarity" and i + 1 < len(args):
                try:
                    similarity_threshold = float(args[i + 1])
                    args.pop(i)  # 移除 --similarity
                    args.pop(i)  # 移除阈值值
                except ValueError:
                    print("❌ 相似度阈值必须是0-1之间的数字")
                    return
            elif args[i] == "--max" and i + 1 < len(args):
                try:
                    max_results = int(args[i + 1])
                    args.pop(i)  # 移除 --max
                    args.pop(i)  # 移除数量值
                except ValueError:
                    print("❌ 最大结果数必须是正整数")
                    return
            elif args[i] == "--history":
                # 显示history文件信息
                try:
                    query_handler = DataQueryHandler()
                    if json_output:
                        json_result = query_handler.get_history_files_json()
                        print(json_result)
                    else:
                        cli_show_history(query_handler)
                except Exception as e:
                    print(f"❌ 错误: {e}")
                return
            else:
                i += 1
        
        if args:
            # 命令行模式 - 查询功能
            search_term = " ".join(args)
            try:
                query_handler = DataQueryHandler()
                if json_output:
                    # 输出JSON格式
                    json_result = query_handler.get_query_results_json(
                        search_term, include_context=include_context,
                        similarity_threshold=similarity_threshold, max_results=max_results
                    )
                    print(json_result)
                else:
                    # 输出友好格式
                    cli_query(query_handler, search_term, include_context, similarity_threshold)
            except Exception as e:
                print(f"❌ 错误: {e}")
        else:
            print("❌ 请提供查询关键词")
            print("用法: python data_query.py [选项] <查询关键词>")
            print("选项:")
            print("  --json: 输出JSON格式")
            print("  --context: 包含上下文推荐")
            print("  --similarity <0-1>: 设置相似度阈值 (默认: 0.15)")
            print("  --max <数量>: 设置最大返回结果数 (默认: 20)")
            print("  --history: 显示history目录文件信息")
            print("示例:")
            print("  python data_query.py --similarity 0.5 --max 10 产品")
            print("  python data_query.py --context --json 技术规格")
    else:
        print("❌ 请提供查询关键词")
        print("用法: python data_query.py [选项] <查询关键词>")
        print("选项:")
        print("  --json: 输出JSON格式")
        print("  --context: 包含上下文推荐")
        print("  --similarity <0-1>: 设置相似度阈值 (默认: 0.3)")
        print("  --max <数量>: 设置最大返回结果数 (默认: 20)")
        print("  --history: 显示history目录文件信息")
        print("示例:")
        print("  python data_query.py --similarity 0.5 --max 10 产品")
        print("  python data_query.py --context --json 技术规格")


if __name__ == "__main__":
    main()