"""
Google Drive Access Troubleshooting Script

This script helps diagnose why your service account might not have access to folders.
"""

from google_drive_reader import GoogleDriveReader
import json


def check_service_account_info():
    """Check service account information."""
    print("🔍 Checking Service Account Information")
    print("=" * 50)
    
    try:
        with open('service_account.json', 'r') as f:
            service_account_data = json.load(f)
        
        client_email = service_account_data.get('client_email', 'Not found')
        project_id = service_account_data.get('project_id', 'Not found')
        
        print(f"📧 Service Account Email: {client_email}")
        print(f"🏗️  Project ID: {project_id}")
        print(f"🔑 Key Type: {service_account_data.get('type', 'Unknown')}")
        
        return client_email
        
    except FileNotFoundError:
        print("❌ service_account.json not found!")
        return None
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return None


def test_drive_access():
    """Test basic Drive access and permissions."""
    print("\n🔍 Testing Drive Access")
    print("=" * 50)
    
    reader = GoogleDriveReader()
    
    if not reader.authenticate():
        print("❌ Authentication failed!")
        return False
    
    print("✅ Authentication successful!")
    
    # Test 1: Try to list all files (not just folders)
    print("\n📄 Testing file access...")
    try:
        # Search for any files, not just folders
        results = reader.service.files().list(
            pageSize=10,
            fields="nextPageToken, files(id, name, mimeType, parents)"
        ).execute()
        
        files = results.get('files', [])
        print(f"Found {len(files)} files total")
        
        if files:
            print("✅ Can access files! Here are some examples:")
            for file in files[:3]:
                print(f"  - {file['name']} ({file.get('mimeType', 'Unknown type')})")
        else:
            print("⚠️  No files found - this might be normal if Drive is empty")
            
    except Exception as e:
        print(f"❌ Error accessing files: {e}")
        return False
    
    # Test 2: Try to list folders with different queries
    print("\n📁 Testing folder access with different methods...")
    
    # Method 1: List folders in root
    try:
        folders_root = reader.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents",
            pageSize=10,
            fields="files(id, name, parents)"
        ).execute()
        
        root_folders = folders_root.get('files', [])
        print(f"Method 1 - Root folders: {len(root_folders)} found")
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: List all folders (not just root)
    try:
        folders_all = reader.service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            pageSize=10,
            fields="files(id, name, parents)"
        ).execute()
        
        all_folders = folders_all.get('files', [])
        print(f"Method 2 - All folders: {len(all_folders)} found")
        
        if all_folders:
            print("✅ Found folders! Here are some:")
            for folder in all_folders[:3]:
                print(f"  - {folder['name']} (ID: {folder['id']})")
                
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    return True


def check_shared_folders():
    """Check if there are any shared folders."""
    print("\n🔍 Checking for Shared Folders")
    print("=" * 50)
    
    reader = GoogleDriveReader()
    
    if not reader.authenticate():
        return False
    
    try:
        # Look for files that might be in shared folders
        results = reader.service.files().list(
            q="sharedWithMe=true",
            pageSize=10,
            fields="files(id, name, mimeType, parents, owners)"
        ).execute()
        
        shared_files = results.get('files', [])
        print(f"Found {len(shared_files)} shared files/folders")
        
        if shared_files:
            print("✅ Found shared items:")
            for item in shared_files:
                print(f"  - {item['name']} ({item.get('mimeType', 'Unknown')})")
        else:
            print("⚠️  No shared items found")
            
    except Exception as e:
        print(f"❌ Error checking shared items: {e}")


def provide_solution_steps(service_account_email):
    """Provide step-by-step solution."""
    print("\n🛠️  SOLUTION STEPS")
    print("=" * 50)
    
    print("To give your service account access to folders:")
    print()
    print("1. 📧 Your service account email is:")
    print(f"   {service_account_email}")
    print()
    print("2. 📁 Go to Google Drive in your browser")
    print("3. 🖱️  Right-click on a folder you want to share")
    print("4. 👥 Click 'Share' or 'Share with others'")
    print("5. 📝 Add this email address:")
    print(f"   {service_account_email}")
    print("6. ✅ Give it 'Viewer' permissions")
    print("7. 📤 Click 'Send'")
    print()
    print("8. 🔄 Run this script again to test access")
    print()
    print("💡 TIP: You can share your entire 'My Drive' folder")
    print("   or specific subfolders - whatever you prefer!")


def main():
    """Main troubleshooting function."""
    print("🔧 Google Drive Access Troubleshooter")
    print("=" * 60)
    
    # Step 1: Check service account info
    service_email = check_service_account_info()
    
    if not service_email:
        print("\n❌ Cannot proceed without service account information")
        return
    
    # Step 2: Test basic access
    if not test_drive_access():
        print("\n❌ Basic Drive access failed")
        return
    
    # Step 3: Check for shared folders
    check_shared_folders()
    
    # Step 4: Provide solution
    provide_solution_steps(service_email)
    
    print("\n🎯 Next Steps:")
    print("1. Share a folder with your service account")
    print("2. Run: python folder_explorer_example.py")
    print("3. You should see your folders listed!")


if __name__ == "__main__":
    main()
