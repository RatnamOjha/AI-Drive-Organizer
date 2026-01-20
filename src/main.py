# src/main.py
from src.auth import authenticate
from src.file_extractor import extract_text_from_file
from src.classifier import classify_file, load_categories
from src.drive_manager import get_or_create_folder, move_file

def main():
    print("🚀 Starting Google Drive Organizer...")
    service = authenticate()
    
    # Fetch files
    results = service.files().list(
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    files = results.get('files', [])
    
    if not files:
        print("📭 No files found.")
        return
    
    # Create category folders FIRST
    categories = list(load_categories().keys()) + ["Uncategorized"]
    folder_ids = {}
    for cat in categories:
        folder_ids[cat] = get_or_create_folder(service, cat)
    
    # Process each file
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            continue
            
        # 🔍 DEBUG: Show real filename and content
        print(f"\n🔍 DEBUG: Raw filename from Drive = '{file['name']}'")
        print(f"   Repr: {repr(file['name'])}")
        
        text = extract_text_from_file(service, file)
        print(f"   Extracted text preview: {repr(text[:60])}")
        
        category = classify_file(text, file['name'])
        print(f"   ➤ Classified as: {category}\n")
        
        # Move file
        success = move_file(service, file['id'], folder_ids[category])
        if success:
            print(f"✅ Moved '{file['name']}' → {category}")
        else:
            print(f"❌ Failed to move '{file['name']}'")

if __name__ == '__main__':
    main()

