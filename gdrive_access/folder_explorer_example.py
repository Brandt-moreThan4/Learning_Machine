"""
Google Drive Folder Explorer Example

This script demonstrates how to explore your Google Drive folder structure
and search for files in specific folders.
"""

from google_drive_reader import GoogleDriveReader


def explore_drive_structure():
    """Explore and display your Drive folder structure."""
    print("🔍 Google Drive Folder Explorer")
    print("=" * 50)
    
    # Initialize reader
    reader = GoogleDriveReader()
    
    # Authenticate
    if not reader.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("✅ Successfully authenticated!")
    
    # 1. List all top-level folders
    print("\n📁 Top-level folders you have access to:")
    print("-" * 40)
    folders = reader.list_folders()
    
    if not folders:
        print("No folders found. You may need to share folders with your service account.")
        return
    
    for i, folder in enumerate(folders, 1):
        print(f"{i:2d}. {folder['name']} (ID: {folder['id']})")
    
    # 2. Explore folder structure (2 levels deep)
    print(f"\n📁 Folder structure (showing first 2 levels):")
    print("-" * 50)
    reader.explore_folder_structure(max_depth=2)
    
    # 3. Show how to search in specific folders
    print(f"\n🔍 How to search in specific folders:")
    print("-" * 50)
    
    if folders:
        # Use the first folder as an example
        example_folder = folders[0]
        print(f"Example: Searching for HTML files in '{example_folder['name']}'")
        
        # Search for HTML files in this folder
        html_files = reader.search_in_folder(example_folder['id'], 'html', max_files=5)
        
        if html_files:
            print(f"Found {len(html_files)} HTML files:")
            for file_info in html_files:
                print(f"  - {file_info['name']} ({file_info.get('size', 'Unknown')} bytes)")
        else:
            print("No HTML files found in this folder.")
    
    return folders


def search_specific_folder(folder_id: str, file_type: str = "html"):
    """Search for files in a specific folder."""
    print(f"\n🔍 Searching for {file_type} files in folder: {folder_id}")
    print("-" * 50)
    
    reader = GoogleDriveReader()
    
    if not reader.authenticate():
        print("❌ Authentication failed!")
        return
    
    # Get folder path for context
    folder_path = reader.get_folder_path(folder_id)
    print(f"📁 Folder path: {folder_path}")
    
    # Search for files
    files = reader.search_in_folder(folder_id, file_type, max_files=20)
    
    if files:
        print(f"\nFound {len(files)} {file_type} files:")
        for i, file_info in enumerate(files, 1):
            print(f"{i:2d}. {file_info['name']} ({file_info.get('size', 'Unknown')} bytes)")
    else:
        print(f"No {file_type} files found in this folder.")
    
    return files


def download_and_save_from_folder(folder_id: str, file_type: str = "html"):
    """Download and save files from a specific folder."""
    print(f"\n💾 Downloading and saving {file_type} files from folder...")
    print("-" * 50)
    
    reader = GoogleDriveReader()
    
    if not reader.authenticate():
        print("❌ Authentication failed!")
        return
    
    # Get files in the folder
    files = reader.search_in_folder(folder_id, file_type, max_files=10)
    
    if not files:
        print(f"No {file_type} files found.")
        return
    
    print(f"Downloading {len(files)} files...")
    
    downloaded_files = []
    for file_info in files:
        print(f"📥 Downloading: {file_info['name']}")
        
        # Download content
        content = reader.download_file_content(file_info['id'])
        
        if content:
            # Save to output folder
            saved_path = reader.save_html_file(
                file_info['name'], 
                content, 
                file_info['id']
            )
            
            if saved_path:
                downloaded_files.append({
                    'original_name': file_info['name'],
                    'saved_path': saved_path,
                    'size': file_info.get('size', 'Unknown')
                })
    
    print(f"\n✅ Successfully downloaded {len(downloaded_files)} files!")
    print(f"📁 Files saved to: {reader.output_folder}")
    
    return downloaded_files


def main():
    """Main function with interactive examples."""
    print("🚀 Google Drive Folder Explorer")
    print("=" * 60)
    
    # Step 1: Explore structure
    folders = explore_drive_structure()
    
    if not folders:
        return
    
    # Step 2: Interactive folder selection
    print(f"\n🎯 Interactive Examples:")
    print("-" * 30)
    
    # Example 1: Search in first folder
    if folders:
        first_folder = folders[0]
        print(f"\n1. Searching in '{first_folder['name']}':")
        search_specific_folder(first_folder['id'], 'html')
    
    # Example 2: Download from first folder
    if folders:
        print(f"\n2. Downloading from '{first_folder['name']}':")
        download_and_save_from_folder(first_folder['id'], 'html')
    
    print(f"\n🎉 Exploration complete!")
    print(f"\n💡 Tips:")
    print(f"   - Use folder IDs to search specific folders")
    print(f"   - Share folders with your service account email")
    print(f"   - Use reader.get_folder_path(folder_id) to get full paths")
    print(f"   - Use reader.search_in_folder(folder_id, 'html') for specific searches")


if __name__ == "__main__":
    main()
