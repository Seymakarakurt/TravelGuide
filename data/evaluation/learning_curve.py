# plot_learning_curve.py

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import learning_curve
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

# Lade die Daten
with open('data/evaluation/metrics.json', 'r') as f:
    data = json.load(f)

messages = [i['message'] for i in data['interactions']]
qualities = [i['response_quality']['overall_quality'] for i in data['interactions']]

# Feature + Target
X = np.array(messages)
y = np.array(qualities)

# Pipeline: TF-IDF + Regression
pipeline = make_pipeline(
    TfidfVectorizer(),
    LinearRegression()
)

# Berechne Lernkurve
train_sizes, train_scores, test_scores = learning_curve(
    pipeline, X, y,
    cv=5,
    scoring='r2',
    train_sizes=np.linspace(0.1, 1.0, 5),
    n_jobs=-1
)

# Mittelwert + Std-Abweichung
train_mean = np.mean(train_scores, axis=1)
train_std = np.std(train_scores, axis=1)
test_mean = np.mean(test_scores, axis=1)
test_std = np.std(test_scores, axis=1)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(train_sizes, train_mean, 'o-', label='Training Score')
plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1)
plt.plot(train_sizes, test_mean, 'o-', label='Cross-validation Score')
plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1)
plt.title('Learning Curve (Text → Overall Quality)')
plt.xlabel('Training Samples')
plt.ylabel('R² Score')
plt.legend(loc='best')
plt.grid()
plt.show()