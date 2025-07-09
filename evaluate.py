from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def evaluate_model(predictions, test_Y):
    # 计算准确率
    accuracy = accuracy_score(test_Y, predictions)
    print(f"Accuracy: {accuracy:.4f}")

    # 计算精确率
    precision = precision_score(test_Y, predictions)
    print(f"Precision: {precision:.4f}")

    # 计算召回率
    recall = recall_score(test_Y, predictions)
    print(f"Recall: {recall:.4f}")

    # 计算 F1-Score
    f1 = f1_score(test_Y, predictions)
    print(f"F1-Score: {f1:.4f}")

    # 混淆矩阵
    cm = confusion_matrix(test_Y, predictions)
    print("Confusion Matrix:")
    print(cm)