import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# 计算惯性
def calculate_inertia(X, centroids, labels):
    inertia = 0
    for i in range(len(centroids)):
        inertia += np.sum((X[labels == i] - centroids[i])**2)
    return inertia

# 可视化聚类结果并保存图形
def plot_clusters(X, labels, centroids):
    plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis')
    plt.scatter(centroids[:, 0], centroids[:, 1], c='red', marker='X', s=200, label="Centroids")
    plt.legend()
    plt.savefig("clusters_plot.png")  # 保存图像为 PNG 文件
    plt.close()  # 关闭当前图形，避免图形堆积

# 使用 PCA 可视化并保存图形
def plot_pca(X, labels):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap='viridis')
    plt.savefig("pca_plot.png")  # 保存图像为 PNG 文件
    plt.close()  # 关闭当前图形
