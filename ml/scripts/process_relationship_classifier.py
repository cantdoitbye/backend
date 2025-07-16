
import os
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

data = {
    'relation': ['Relatives', 'Relatives', 'Professional', 'Professional', 'Friend', 'Friend', 'Relatives', 'Professional', 'Relatives'],
    'sub_relation_name': ['Father', 'Cousin', 'Employee', 'Neighbour', 'Friend', 'Pen pal', 'Grandchild', 'Mentor', 'Child'],
    'directionality': ['Bidirectional', 'Unidirectional', 'Bidirectional', 'Unidirectional', 'Unidirectional', 'Unidirectional', 'Bidirectional', 'Bidirectional', 'Bidirectional'],
    'approval_required': [True, True, True, True, True, True, True, True, True],
    'circle': ['Inner', 'Outer', 'Outer', 'Outer', 'Universal', 'Universal', 'Inner', 'Outer', 'Inner']
}

df = pd.DataFrame(data)
le_relation = LabelEncoder()
le_directionality = LabelEncoder()
le_circle = LabelEncoder()

df['relation'] = le_relation.fit_transform(df['relation'])
df['directionality'] = le_directionality.fit_transform(df['directionality'])
df['circle'] = le_circle.fit_transform(df['circle'])

X = df[['relation', 'directionality', 'approval_required']]
y = df['circle']  

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")

model_dir = os.path.join('ml', 'model')
if not os.path.exists(model_dir):
    os.makedirs(model_dir)

joblib.dump(clf, os.path.join(model_dir, 'relationship_classifier_model.pkl'))
joblib.dump(le_relation, os.path.join(model_dir, 'relation_encoder.pkl'))
joblib.dump(le_directionality, os.path.join(model_dir, 'directionality_encoder.pkl'))

print(f"Model and encoders saved to {model_dir}")
