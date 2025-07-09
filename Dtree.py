# Dtree.py

import math
from preprocess import load_and_preprocess_data
from evaluate import evaluate_model

class Dtree():
    def __init__(self, max_depth=None):
        self.tree = None
        self.max_depth = max_depth  # 最大深度
    
    def _entropy(self, Y):
        n = len(Y)
        unique_values, counts = list(set(Y)), [Y.count(value) for value in set(Y)]
        prob = [count / n for count in counts]
        return -sum(p * (p if p == 0 else math.log2(p)) for p in prob)

    def _information_gain(self, X, Y, feature_index):
        entropy_before = self._entropy(Y)
        values = [X[i][feature_index] for i in range(len(X))]
        unique_values = list(set(values))
        total_entropy = 0
        for value in unique_values:
            subset_Y = [Y[i] for i in range(len(X)) if X[i][feature_index] == value]
            total_entropy += len(subset_Y) / len(Y) * self._entropy(subset_Y)
        return entropy_before - total_entropy

    def _best_split(self, X, Y):
        best_gain = -1
        best_feature = None
        for feature_index in range(len(X[0])):
            gain = self._information_gain(X, Y, feature_index)
            if gain > best_gain:
                best_gain = gain
                best_feature = feature_index
        return best_feature

    def _build_tree(self, X, Y, depth=0):
        if self.max_depth and depth >= self.max_depth:
            return max(set(Y), key=Y.count)  # 返回多数类标签
        
        if len(set(Y)) == 1:  # 所有标签都相同
            return Y[0]

        if len(X[0]) == 0:  # 没有特征了，返回多数类标签
            return max(set(Y), key=Y.count)

        best_feature = self._best_split(X, Y)
        tree = {best_feature: {}}

        values = [X[i][best_feature] for i in range(len(X))]
        unique_values = set(values)
        
        for value in unique_values:
            subset_X = [X[i] for i in range(len(X)) if X[i][best_feature] == value]
            subset_Y = [Y[i] for i in range(len(Y)) if X[i][best_feature] == value]
            tree[best_feature][value] = self._build_tree(subset_X, subset_Y, depth + 1)
        
        return tree

    def fit(self, X:list, Y:list) -> None:
        self.tree = self._build_tree(X, Y)

    def predict(self, X:list) -> list:
        def predict_one(tree, x):
            if isinstance(tree, dict):
                feature_index = list(tree.keys())[0]
                feature_value = x[feature_index]
                return predict_one(tree[feature_index].get(feature_value), x)
            return tree

        predictions = [predict_one(self.tree, x) for x in X]
        return predictions

def main(train_X, train_Y, test_X, test_Y):
    model = Dtree(max_depth=3)
    model.fit(train_X, train_Y)
    predictions = model.predict(test_X)
    
    # 将预测结果写入文件
    with open('predictions.txt', 'w') as f:
        for prediction in predictions:
            f.write(f"{prediction}\n")  # 每个预测结果写入一行
    
    # 调用评估函数
    evaluate_model(predictions, test_Y)

# 加载数据并预处理
train_X, test_X, train_Y, test_Y = load_and_preprocess_data('data/spam.csv')
print(f"Training data size: {len(train_X)}")
print(f"Test data size: {len(test_X)}")

# 调用 main 函数进行训练、预测并评估
main(train_X, train_Y, test_X, test_Y)
