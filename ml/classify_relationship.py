import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

def classify_relationship(
    relation: str, 
    sub_relation_name: str,
    directionality: str, 
    approval_required: bool,
    clf: RandomForestClassifier,
    le_relation: LabelEncoder,
    le_directionality: LabelEncoder
) -> str:
    try:
        relation_encoded = le_relation.transform([relation])[0]
        directionality_encoded = le_directionality.transform([directionality])[0]
        approval_required_encoded = 1 if approval_required else 0
        input_data = pd.DataFrame({
            'relation': [relation_encoded],
            'directionality': [directionality_encoded],
            'approval_required': [approval_required_encoded]
        })
        predicted_circle_index = clf.predict(input_data)[0]
        circle_mapping = ['Inner', 'Outer', 'Universal']
        return circle_mapping[predicted_circle_index]

    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return "Unknown"

def main():
    try:
        clf = joblib.load('ml/model/relationship_classifier_model.pkl')
        le_relation = joblib.load('ml/model/relation_encoder.pkl')
        le_directionality = joblib.load('ml/model/directionality_encoder.pkl')

        circle_result = classify_relationship(
            relation="Friend", 
            sub_relation_name="Pen pal", 
            directionality="Unidirectional", 
            approval_required=True, 
            clf=clf, 
            le_relation=le_relation, 
            le_directionality=le_directionality
        )
        print(f"The predicted circle for 'Pen pal' is: {circle_result}")

        circle_result = classify_relationship(
            relation="Professional", 
            sub_relation_name="Employee", 
            directionality="Unidirectional", 
            approval_required=True, 
            clf=clf, 
            le_relation=le_relation, 
            le_directionality=le_directionality
        )
        print(f"The predicted circle for 'Employee' is: {circle_result}")

        circle_result = classify_relationship(
            relation="Relatives", 
            sub_relation_name="Cousin", 
            directionality="Bidirectional", 
            approval_required=True, 
            clf=clf, 
            le_relation=le_relation, 
            le_directionality=le_directionality
        )
        print(f"The predicted circle for 'Cousin' is: {circle_result}")

    except FileNotFoundError as e:
        print(f"Error: {e}. Ensure the model and encoders are loaded correctly.")

if __name__ == "__main__":
    main()
