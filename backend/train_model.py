import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

# load dataset
df = pd.read_csv("ml_dataset.csv")

# features + target
X = df.drop("risk_profile", axis=1)
y = df["risk_profile"]

# encode labels
le = LabelEncoder()
y = le.fit_transform(y)

# split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# train
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# accuracy
acc = model.score(X_test, y_test)
print(f"Accuracy: {acc:.2f}")

# save model + encoder
joblib.dump(model, "ai_model.pkl")
joblib.dump(le, "label_encoder.pkl")

print("Model saved!")