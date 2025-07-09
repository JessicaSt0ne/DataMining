# run_comparison.py
print("--- run_comparison.py 脚本开始执行 ---")

import sys
import os
import time
import tracemalloc # 用于内存分析 (可选)

# --- 1. 定义项目根目录并添加到 sys.path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"调试: 项目根目录 PROJECT_ROOT 计算为: {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src import fp_growth_standard as fp_std
    from src import fp_growth_optimized as fp_opt
    print("--- src 模块导入成功！ ---")
except ImportError as e:
    print(f"错误：无法导入 src 包中的模块。异常: {e}")
    sys.exit(1)

def load_transactions_from_file(filepath):
    transactions = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line: 
                    transactions.append(stripped_line.split(' '))
    except FileNotFoundError:
        raise 
    return transactions

def prepare_dataset_for_fpgrowth(transaction_list):
    dataset_dict = {}
    if transaction_list is None:
        return dataset_dict
    for transaction in transaction_list:
        frozen_transaction = frozenset(transaction)
        dataset_dict[frozen_transaction] = dataset_dict.get(frozen_transaction, 0) + 1
    return dataset_dict

def run_single_algorithm_experiment(algorithm_module, algorithm_name, 
                                    prepared_fpgrowth_dataset, min_support_count,
                                    is_standard_version=True):
    print(f"\n--- 运行: {algorithm_name} (最小支持度计数: {min_support_count}) ---")
    results = {
        "algorithm": algorithm_name,
        "min_support_count": min_support_count,
        "tree_build_time": -1.0,
        "mining_time": -1.0, 
        "total_time": -1.0,
        "num_frequent_itemsets": 0,
        "frequent_itemsets": [],
        "error": None,
        "fp_tree_nodes": 0, # 新增：FP树节点数
        "peak_memory_usage_mb": 0.0 # 新增：峰值内存占用 (MB)
    }
    fp_tree, header_table = None, None
    num_tree_nodes_val = 0

    tracemalloc.start() # 开始跟踪内存分配

    try:
        start_time_tree = time.time()
        if is_standard_version:
            # create_tree_standard 现在返回 (tree, header, num_nodes)
            fp_tree, header_table, num_tree_nodes_val = algorithm_module.create_tree_standard(
                prepared_fpgrowth_dataset, min_support_count
            )
        else:
            # create_tree_optimized 现在返回 (tree, header, num_nodes)
            fp_tree, header_table, num_tree_nodes_val = algorithm_module.create_tree_optimized(
                prepared_fpgrowth_dataset, min_support_count
            )
        end_time_tree = time.time()
        results["tree_build_time"] = end_time_tree - start_time_tree
        results["fp_tree_nodes"] = num_tree_nodes_val # 存储节点数
        print(f"  建树时间: {results['tree_build_time']:.4f} 秒")
        print(f"  FP树节点数: {results['fp_tree_nodes']}") # 打印节点数
        
        frequent_itemsets_list = []
        time_spent_on_cond_bases = 0 # 初始化一个变量来尝试估算
        
        if fp_tree and header_table :
            # 对于“条件模式基生成时间”的估算：
            # 1. 可以在 mine_tree 函数内部，每次调用 find_prefix_path 时计时，并累加。
            #    这需要修改 mine_tree 函数使其能返回这个时间。
            # 2. 简化：可以认为挖掘时间主要消耗在条件模式基生成和条件树构建上。
            #    这里我们暂时不单独分离它，它包含在 "mining_time" 中。
            #    如果需要更精确，需要深入修改 mine_tree_... 函数。

            print(f"  开始挖掘，FP树根节点: {fp_tree.name if hasattr(fp_tree, 'name') else fp_tree.get_representation() if hasattr(fp_tree, 'get_representation') else 'N/A'}, 头指针表项数: {len(header_table)}")
            start_time_mine = time.time()
            if is_standard_version:
            # create_tree_standard 现在返回 (tree, header, num_nodes)
                fp_tree, header_table, num_tree_nodes_val = algorithm_module.create_tree_standard( # <--- 修改这里
                prepared_fpgrowth_dataset, min_support_count
            )
            else:
            # create_tree_optimized 现在返回 (tree, header, num_nodes)
                fp_tree, header_table, num_tree_nodes_val = algorithm_module.create_tree_optimized( # <--- 修改这里
                prepared_fpgrowth_dataset, min_support_count
            )
            end_time_mine = time.time()
            results["mining_time"] = end_time_mine - start_time_mine
            print(f"  挖掘时间 (主要包含条件模式基生成和递归挖掘): {results['mining_time']:.4f} 秒")
            results["frequent_itemsets"] = sorted([sorted(list(s)) for s in frequent_itemsets_list]) # 确保排序以便比较
            results["num_frequent_itemsets"] = len(frequent_itemsets_list)
            print(f"  发现频繁项集数量: {results['num_frequent_itemsets']}")
        elif not fp_tree : 
            print(f"  警告: FP树未能构建 (fp_tree is None)，跳过挖掘。")
            results["mining_time"] = 0 # 确保有值
        elif not header_table: 
            print(f"  警告: 头指针表为空或未构建 (header_table is None or empty)，跳过挖掘。")
            results["mining_time"] = 0 # 确保有值
        
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        results["peak_memory_usage_mb"] = peak_mem / 1024 / 1024
        print(f"  峰值内存占用 (估算): {results['peak_memory_usage_mb']:.2f} MB")
        
        if results["tree_build_time"] >= 0 and results["mining_time"] >= 0:
             results["total_time"] = results["tree_build_time"] + results["mining_time"]
        elif results["tree_build_time"] >=0: # 只有建树时间
             results["total_time"] = results["tree_build_time"]
        else:
             results["total_time"] = 0.0 

        print(f"  总执行时间: {results['total_time']:.4f} 秒")

    except Exception as e:
        print(f"  执行 {algorithm_name} 时发生错误: {e}")
        results["error"] = str(e)
        current_mem_err, peak_mem_err = tracemalloc.get_traced_memory() # 仍然获取内存信息
        results["peak_memory_usage_mb"] = peak_mem_err / 1024 / 1024
        import traceback
        traceback.print_exc()
    finally:
        tracemalloc.stop() # 停止跟踪
        tracemalloc.clear_traces() # 清除跟踪记录，为下一次运行做准备
    return results

def compare_frequent_itemsets(std_results, opt_results):
    # ... (此函数保持不变，它比较的是最终的频繁项集列表) ...
    if std_results["error"] or opt_results["error"]:
        print("\n--- 结果正确性比较 ---")
        print("  由于一个或两个算法执行出错，无法进行正确性比较。")
        return
    
    std_sets_for_comp = set()
    if std_results.get("frequent_itemsets"): 
        try:
            std_sets_for_comp = set(tuple(sorted(list(itemset))) for itemset in std_results["frequent_itemsets"])
        except TypeError as e:
            print(f"  比较错误：标准版结果中的项集无法转换为元组进行比较 - {e}")
            return

    opt_sets_for_comp = set()
    if opt_results.get("frequent_itemsets"): 
        try:
            opt_sets_for_comp = set(tuple(sorted(list(itemset))) for itemset in opt_results["frequent_itemsets"])
        except TypeError as e:
            print(f"  比较错误：优化版结果中的项集无法转换为元组进行比较 - {e}")
            return

    print("\n--- 结果正确性比较 ---")
    if std_sets_for_comp == opt_sets_for_comp:
        print("  正确！标准版和优化版算法产生的频繁项集完全一致。")
    else:
        print("  错误！标准版和优化版算法产生的频繁项集不一致。")
        if len(std_sets_for_comp) != len(opt_sets_for_comp):
            print(f"    项集数量不同: 标准版 {len(std_sets_for_comp)}, 优化版 {len(opt_sets_for_comp)}")
        
        diff_std_opt = std_sets_for_comp - opt_sets_for_comp
        if diff_std_opt:
            print(f"    仅在标准版中出现的项集 (前5个): {list(diff_std_opt)[:5]}")
        
        diff_opt_std = opt_sets_for_comp - std_sets_for_comp
        if diff_opt_std:
            print(f"    仅在优化版中出现的项集 (前5个): {list(diff_opt_std)[:5]}")


# --- 主执行逻辑 ---
if __name__ == "__main__":
    print(f"--- 进入 __main__ 执行块 ---") 

    # --- 配置实验参数 ---
    datasets_config = [
        {
            "name": "小型测试数据集",
            "path": os.path.join(PROJECT_ROOT, "data", "small_dataset.txt"), 
            "min_supports": [2, 3] 
        },
        {
            "name": "Mushroom数据集 (预处理后)",
            "path": os.path.join(PROJECT_ROOT, "data", "mushroom", "mushroom_transactions.txt"), 
            # 调整min_supports以测试极端场景
            # 较低的min_sup会导致树更复杂，挖掘时间更长
            # 较高的min_sup会导致树更简单，挖掘时间更短
            "min_supports": [3000, 5000, 7000] # 例如：常规, 较高(更稀疏), 非常高(极端稀疏)
        },
    ]

    all_experiment_results = [] 

    for dataset_info in datasets_config:
        dataset_name = dataset_info["name"]
        dataset_filepath = dataset_info["path"] 

        print(f"\n======================================================")
        print(f"开始处理数据集: {dataset_name} (路径: {dataset_filepath})") 
        print(f"======================================================")

        raw_transactions = None
        try:
            raw_transactions = load_transactions_from_file(dataset_filepath)
            print(f"  成功加载 {len(raw_transactions)} 条事务从 {dataset_name}")
        except FileNotFoundError: 
            print(f"错误: 主逻辑中确认数据文件 '{dataset_filepath}' 未找到。请检查路径和文件名。")
            continue 

        if raw_transactions is None or not raw_transactions : 
            print(f"无法加载数据集 {dataset_name} 或数据集为空，跳过。")
            continue

        fpgrowth_input_data = prepare_dataset_for_fpgrowth(raw_transactions)
        if not fpgrowth_input_data:
            print(f"数据集 {dataset_name} 预处理后为空，跳过。")
            continue
        print(f"  数据集预处理完成，转换得到 {len(fpgrowth_input_data)} 条唯一事务（带计数）。")

        for min_sup in dataset_info["min_supports"]:
            # 标准版
            TreeNode = getattr(fp_std, 'TreeNode', None) # 获取 TreeNode 类
            if TreeNode: TreeNode._node_id_counter = 0 # 重置标准版节点ID计数器
            if hasattr(fp_std, 'conditional_tree_id_standard'): # 重置条件树ID计数器
                fp_std.conditional_tree_id_standard = 0

            std_res = run_single_algorithm_experiment(
                fp_std, "标准FP-Growth", fpgrowth_input_data, min_sup, is_standard_version=True
            )
            std_res["dataset"] = dataset_name 
            all_experiment_results.append(std_res)

            # 优化版
            HybridTreeNode = getattr(fp_opt, 'HybridTreeNode', None) # 获取 HybridTreeNode 类
            if HybridTreeNode: HybridTreeNode._node_id_counter = 0 # 重置优化版节点ID计数器
            if hasattr(fp_opt, 'conditional_tree_id_optimized_global'): # 重置条件树ID计数器
                 fp_opt.conditional_tree_id_optimized_global = 0


            opt_res = run_single_algorithm_experiment(
                fp_opt, "优化FP-Growth (b)", fpgrowth_input_data, min_sup, is_standard_version=False
            )
            opt_res["dataset"] = dataset_name 
            all_experiment_results.append(opt_res)

            compare_frequent_itemsets(std_res, opt_res)

    print("\n\n================== 实验结果汇总 ==================")
    # 打印表头
    header = "| {:<25} | {:<20} | {:<10} | {:<10} | {:<10} | {:<10} | {:<12} | {:<10} | {:<15} |"
    separator = "-" * 150
    print(separator)
    print(header.format("数据集", "算法", "MinSup", "树节点数", "建树时间(s)", "挖掘时间(s)", "总时间(s)", "频繁项数", "峰值内存(MB)"))
    print(separator)

    for res in all_experiment_results:
        if res["error"]:
            print(header.format(
                res.get('dataset', 'N/A'), 
                res['algorithm'], 
                res['min_support_count'], 
                "N/A", "N/A", "N/A", "N/A", "N/A",
                f"{res.get('peak_memory_usage_mb', 0.0):.2f}"
            ) + f" Error: {res['error']}")
        else:
            print(header.format(
                res.get('dataset', 'N/A'), 
                res['algorithm'], 
                res['min_support_count'], 
                res.get('fp_tree_nodes', 'N/A'), 
                f"{res['tree_build_time']:.4f}", 
                f"{res['mining_time']:.4f}", 
                f"{res['total_time']:.4f}", 
                res['num_frequent_itemsets'],
                f"{res.get('peak_memory_usage_mb', 0.0):.2f}"
            ))
    print(separator)
    print("所有实验运行完毕。")