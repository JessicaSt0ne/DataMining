import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer

def load_and_preprocess_data(file_path):
    # 加载数据集
    df = pd.read_csv(file_path, encoding='latin-1')

    # 选择需要的列：短信内容和标签
    df = df[['v1', 'v2']]  # 'v1' 是标签列，'v2' 是短信内容列
    df.columns = ['label', 'message']  # 重命名列

    # 标签转换：'ham' -> 0, 'spam' -> 1
    df['label'] = df['label'].map({'ham': 0, 'spam': 1})

    # 删除包含 NaN 或空白字符串的行
    df = df.dropna(subset=['message'])
    df = df[df['message'].str.strip() != ""]  # 删除空白消息

    # 切分数据：训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(df['message'], df['label'], test_size=0.2, random_state=42)

    # 文本转换：使用词袋模型（CountVectorizer）
    vectorizer = CountVectorizer(stop_words=None)  # 禁用停用词
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # 转换为 list[list[float]] 格式
    X_train_list = X_train_vec.toarray().tolist()  # 转换为列表格式
    X_test_list = X_test_vec.toarray().tolist()    # 转换为列表格式

    # 返回特征矩阵和标签，包括 test_Y
    return X_train_list, X_test_list, y_train.tolist(), y_test.tolist()
