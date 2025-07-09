import numpy as np

def kmeans_plus_plus(X, k):
    centroids = [X[np.random.choice(X.shape[0])]]  # 选择第一个中心点
    for _ in range(1, k):
        distances = np.min(np.linalg.norm(X[:, np.newaxis] - np.array(centroids), axis=2), axis=1)
        squared_distances = distances ** 2
        probabilities = squared_distances / squared_distances.sum()
        next_centroid = X[np.random.choice(X.shape[0], p=probabilities)]
        centroids.append(next_centroid)
    
    return np.array(centroids)
