# src/classifier.py
import json
import os

def load_categories():
    # Get the directory where THIS file lives
    current_dir = os.path.dirname(__file__)
    # Go up to project root, then into assets
    json_path = os.path.join(current_dir, '..', 'assets', 'category_keywords.json')
    with open(json_path, 'r') as f:
        return json.load(f)

# In classifier.py
def classify_file(text, filename):
    full_text = (text + " " + filename).lower()
    categories = load_categories()
    
    scores = {cat: 0 for cat in categories}
    
    for category, keywords in categories.items():
        for kw in keywords:
            if kw in full_text:
                # Give higher weight to longer, specific keywords
                scores[category] += len(kw)
    
    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] > 0 else "Uncategorized"

if __name__ == "__main__":
    print(classify_file("", "Ratnam_resume.pdf"))  # Should return "Academics"
    print(classify_file("", "Untitled document"))  # Should return "Uncategorized"
    print(classify_file("financial statement.pdf", "contract.docx"))  # Should return "finance"