# src/frequent_itemset_mining.py
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
import pandas as pd

# 挖掘频繁项集并生成关联规则
def mine_frequent_itemsets(df, min_support=0.1):
    # 使用 Apriori 算法
    frequent_itemsets_apriori = apriori(df, min_support=min_support, use_colnames=True)
    
    # 使用 FP-Growth 算法
    frequent_itemsets_fpgrowth = fpgrowth(df, min_support=min_support, use_colnames=True)
    
    # 生成关联规则
    rules_apriori = association_rules(frequent_itemsets_apriori, metric="lift", min_threshold=1.0)
    rules_fpgrowth = association_rules(frequent_itemsets_fpgrowth, metric="lift", min_threshold=1.0)

    # 保存结果
    frequent_itemsets_apriori.to_csv('results/frequent_itemsets_apriori.csv', index=False)
    frequent_itemsets_fpgrowth.to_csv('results/frequent_itemsets_fpgrowth.csv', index=False)
    rules_apriori.to_csv('results/association_rules_apriori.csv', index=False)
    rules_fpgrowth.to_csv('results/association_rules_fpgrowth.csv', index=False)

    return frequent_itemsets_apriori, frequent_itemsets_fpgrowth, rules_apriori, rules_fpgrowth

# 示例使用
if __name__ == '__main__':
    # 读取和预处理数据
    df = pd.read_csv('results/processed_mushroom_data.csv')

    # 挖掘频繁项集和关联规则
    mine_frequent_itemsets(df)
