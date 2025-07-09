import numpy as np
from .kmeans_plus_plus import kmeans_plus_plus

def kmeans(X, k, max_iter=100, tol=1e-4, seed=42, init="k-means++"):
    np.random.seed(seed)
    
    # 1. 初始化聚类中心
    if init == "random":
        centroids = X[np.random.choice(X.shape[0], k, replace=False)]
    elif init == "k-means++":
        centroids = kmeans_plus_plus(X, k)
    
    print(f"Running K-Means with {init} initialization...")
    
    # 2. 迭代更新
    for i in range(max_iter):
        labels = assign_labels(X, centroids)
        new_centroids = np.array([X[labels == j].mean(axis=0) for j in range(k)])
        
        # 3. 检查收敛
        if np.linalg.norm(new_centroids - centroids) < tol:
            print(f"Converged after {i + 1} iterations")
            break
        
        centroids = new_centroids
    
    return centroids, labels

def assign_labels(X, centroids):
    distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
    return np.argmin(distances, axis=1)
