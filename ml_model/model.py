from sklearn.tree import DecisionTreeClassifier

# Sample data
X = [
    [100, 1, 1],
    [5000, 2, 2],
    [200, 1, 3]
]

y = ["AES", "ChaCha20", "RSA"]

model = DecisionTreeClassifier()
model.fit(X, y)

print("Model trained!")