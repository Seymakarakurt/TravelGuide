import json
import pandas as pd
import matplotlib.pyplot as plt
import glob

# Alle Feedback-Dateien laden
feedback_files = glob.glob('data/feedback_data/feedback_*.json')
all_feedback = []

for file in feedback_files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        all_feedback.extend(data)

# DataFrame erstellen
df = pd.DataFrame(all_feedback)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Feedback kategorisieren
def categorize_feedback(feedback_list):
    if 'Gut' in feedback_list:
        return 'Gut'
    elif 'Schlecht' in feedback_list:
        return 'Schlecht'
    elif 'Ungenau' in feedback_list:
        return 'Ungenau'
    elif 'Unvollständig' in feedback_list:
        return 'Unvollständig'
    else:
        return 'Neutral'

df['feedback_category'] = df['feedback_types'].apply(categorize_feedback)

# Übersicht: Anzahl je Kategorie (schönes Balkendiagramm)
category_counts = df['feedback_category'].value_counts()

plt.figure(figsize=(8, 5))
bars = plt.bar(category_counts.index, category_counts.values, color=['#4CAF50', '#F44336', '#FF9800', '#9E9E9E', '#2196F3'])
plt.title('Nutzerfeedback Übersicht (alle Kategorien)', fontsize=14)
plt.xlabel('Feedback-Kategorie', fontsize=12)
plt.ylabel('Anzahl', fontsize=12)
plt.xticks(fontsize=11)
plt.yticks(fontsize=11)
plt.grid(axis='y', linestyle='--', alpha=0.5)
for bar in bars:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), int(bar.get_height()), ha='center', va='bottom', fontsize=11)
plt.tight_layout()
plt.savefig('feedback_gesamt_uebersicht.png')
plt.show()