# Manages folders and file moves
def get_or_create_folder(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive').execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            folder_metadata['parents'] = [parent_id]
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

# src/drive_manager.py

def move_file(service, file_id, new_folder_id):
    try:
        # Get current parents
        file = service.files().get(fileId=file_id, fields='parents').execute()
        current_parents = file.get('parents', [])
        
        # If no parents, it's in "My Drive" root → implicit parent is 'root'
        if not current_parents:
            remove_parents = 'root'
        else:
            remove_parents = ','.join(current_parents)
        
        # Move the file
        service.files().update(
            fileId=file_id,
            addParents=new_folder_id,
            removeParents=remove_parents,
            fields='id, parents'
        ).execute()
        return True
        
    except Exception as e:
        print(f"❌ Move failed: {e}")
        return False