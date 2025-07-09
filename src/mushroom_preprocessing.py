# src/mushroom_preprocessing.py
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder

def load_dataset(filepath):
    columns = [
        'class', 'cap-shape', 'cap-surface', 'cap-color', 'bruises', 'odor', 
        'gill-attachment', 'gill-spacing', 'gill-size', 'gill-color', 'stalk-shape', 
        'stalk-root', 'stalk-surface-above-ring', 'stalk-surface-below-ring', 
        'stalk-color-above-ring', 'stalk-color-below-ring', 'veil-type', 'veil-color', 
        'ring-type', 'spore-print-color', 'population', 'habitat'
    ]
    df = pd.read_csv(filepath, names=columns)
    return df

def preprocess_data(df):
    transactions = df.values.tolist()
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_transformed = pd.DataFrame(te_ary, columns=te.columns_)
    
    # 保存转换后的数据为 CSV 文件
    df_transformed.to_csv('results/processed_mushroom_data.csv', index=False)
    return df_transformed

# 运行数据预处理并保存
if __name__ == '__main__':
    filepath = 'data/mushroom.data'  # 数据集文件路径
    df = load_dataset(filepath)
    df_transformed = preprocess_data(df)
    print(df_transformed.head())
