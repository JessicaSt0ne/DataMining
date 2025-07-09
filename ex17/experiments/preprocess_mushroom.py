# preprocess_mushroom.py
import os

def preprocess_mushroom_data(input_filepath, output_filepath):
    """
    Preprocesses the agaricus-lepiota.data file into a transaction format.
    Each feature is combined with its column index to create a unique item.
    Example: if column 2 has value 'x', the item becomes '2x'.
    The first column (class label) can be included or excluded.
    For association rule mining, class labels are often treated as just another item
    or sometimes excluded if the goal is to find rules among features only.
    This version includes the class label as item '0<label>'.
    """
    processed_transactions = []
    print(f"开始预处理文件: {input_filepath}")
    try:
        with open(input_filepath, 'r') as infile:
            for line_num, line in enumerate(infile):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                
                attributes = stripped_line.split(',')
                transaction_items = []
                
                # Process class label (first attribute) - e.g., '0p', '0e'
                if attributes:
                    # transaction_items.append(f"0{attributes[0]}") # Uncomment to include class label as an item '0<value>'
                    # Or, to make it more distinct from other features if they could also be '0' + letter
                    transaction_items.append(f"class={attributes[0]}")


                # Process other attributes
                # Start from index 1 if class label is handled, or 0 if class label is also an item like others
                start_index = 1 # Assuming first attribute was class label
                for i in range(start_index, len(attributes)):
                    # Create an item like "columnIndexAttributeValue", e.g., "1x", "2s"
                    # (using i as column index here for simplicity, can be 0-based or 1-based)
                    # Add 1 to i to make it 1-indexed like common parlance for column numbers
                    # Or keep 0-indexed based on `attributes` list index.
                    # Let's use 1-based attribute index for items (excluding class)
                    item = f"{i}{attributes[i]}" # e.g., attribute at index 1 (second in csv) with value 'x' becomes '1x'
                    transaction_items.append(item)
                
                if transaction_items:
                    processed_transactions.append(" ".join(transaction_items))
            
        with open(output_filepath, 'w') as outfile:
            for transaction_str in processed_transactions:
                outfile.write(transaction_str + "\n")
        print(f"预处理完成。事务已保存到: {output_filepath}")
        print(f"共处理了 {len(processed_transactions)} 条事务。")
        if processed_transactions:
            print(f"示例事务 (第一条): {processed_transactions[0]}")
            if len(processed_transactions) > 1:
                print(f"示例事务 (第二条): {processed_transactions[1]}")

    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_filepath}' 未找到。")
    except Exception as e:
        print(f"预处理过程中发生错误: {e}")

if __name__ == "__main__":
    # 定义项目根目录 (与 run_comparison.py 中的方式类似)
    # PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 如果 preprocess_mushroom.py 在 experiments 目录下
    # 如果 preprocess_mushroom.py 与 run_comparison.py 在同一目录 (experiments), 则：
    # EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
    # PROJECT_ROOT = os.path.dirname(EXPERIMENTS_DIR)
    # 为了简单，我们假设你知道 PROJECT_ROOT
    # 或者你可以硬编码路径或使用相对路径进行测试

    # 假设 preprocess_mushroom.py 位于 ex17/experiments/ 目录下
    # 并且 data 文件夹在 ex17/data/
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root_path = os.path.dirname(current_script_dir) # 这是 ex17/  <--- 修改这里
    # 或者更明确一点，如果你的 preprocess_mushroom.py 和 run_comparison.py 在同一个 'experiments' 文件夹下：
    experiments_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_path = os.path.dirname(experiments_dir) # <--- 修改这里

    input_data_file = os.path.join(project_root_path, "data", "mushroom", "agaricus-lepiota.data") # <--- 修改这里
    output_transaction_file = os.path.join(project_root_path, "data", "mushroom", "mushroom_transactions.txt") # <--- 修改这里

    # 创建输出目录如果它不存在
    output_dir = os.path.dirname(output_transaction_file)
    if not os.path.exists(output_dir):
        print(f"创建目录: {output_dir}")
        os.makedirs(output_dir)

    preprocess_mushroom_data(input_data_file, output_transaction_file)