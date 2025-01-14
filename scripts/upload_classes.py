import csv
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    cred = credentials.Certificate("gpt-advisor-firebase-adminsdk-ct285-8f45ca05e4.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    with open("searchData.csv", "r", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_ref = db.collection("classes").document(row["ClassNumber"])
            doc_ref.set(row)

if __name__ == "__main__":
    main()