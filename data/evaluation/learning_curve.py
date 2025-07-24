import json
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import make_scorer, mean_squared_error, mean_absolute_error, r2_score

# Daten laden
with open('data/evaluation/metrics.json', 'r') as f:
    data = json.load(f)

# DataFrame erstellen
df = pd.DataFrame({
    'response_time': [i.get('response_time', 0) for i in data['interactions']],
    'confidence_score': [i.get('intent_evaluation', {}).get('confidence_score', 0) for i in data['interactions']],
    'api_success': [int(i.get('api_success', False)) for i in data['interactions']],
    'overall_quality': [i.get('response_quality', {}).get('overall_quality', 0) for i in data['interactions']]
})

# Features und Target
X = df[['response_time', 'confidence_score', 'api_success']]
y = df['overall_quality']

# Modell
model = RandomForestRegressor(n_estimators=100, random_state=42)

# Cross-Validation Scores berechnen
scoring = {
    'R2': 'r2',
    'MAE': make_scorer(mean_absolute_error),
    'MSE': make_scorer(mean_squared_error)
}
scores = {name: cross_val_score(model, X, y, cv=5, scoring=score).mean() for name, score in scoring.items()}

# Ausgabe der Model Performance
print("Model Performance (Cross-Validated):")
for metric, value in scores.items():
    print(f"{metric}: {value:.4f}")

# Statistische Übersicht zu overall_quality
print("\nStatistik zu overall_quality:")
print(df['overall_quality'].describe())
print("\nWerteverteilung von overall_quality:")
print(df['overall_quality'].value_counts().sort_index())

# Bild generieren: Balkendiagramm der Scores
plt.figure(figsize=(8, 5))
plt.bar(scores.keys(), scores.values(), color='skyblue')
plt.title('Model Performance (Cross-Validated)')
plt.ylabel('Score')
plt.ylim(0, max(scores.values()) * 1.2)
plt.grid(axis='y')
plt.tight_layout()
plt.savefig('model_performance.png')
plt.show()