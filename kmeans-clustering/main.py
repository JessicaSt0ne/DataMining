import numpy as np
from sklearn.datasets import load_iris
from src.kmeans import kmeans
from src.utils import plot_clusters, plot_pca, calculate_inertia
import matplotlib.pyplot as plt

# 加载 Iris 数据集
iris = load_iris()
X = iris.data
y = iris.target

# 设置不同的 k 值（聚类数）
k_values = range(1, 11)  # k 从 1 到 10
inertia_values = []

# 计算每个 k 值的惯性
for k in k_values:
    centroids, labels = kmeans(X, k)
    inertia = calculate_inertia(X, centroids, labels)
    inertia_values.append(inertia)

# 绘制惯性随 k 值变化的图像
plt.plot(k_values, inertia_values, marker='o')
plt.title('Inertia vs. k')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Inertia')
plt.savefig("inertia_plot.png")  # 保存惯性图
plt.close()

# 选择聚类数 k = 3 来运行 K-Means 算法
k = 3  # 设置聚类个数
centroids, labels = kmeans(X, k)

# 绘制聚类结果并保存为文件
print("Plotting clusters...")
plot_clusters(X, labels, centroids)

# 使用 PCA 降维后可视化并保存为文件
print("Plotting PCA...")
plot_pca(X, labels)
