# Google Drive API Setup Instructions (Automated/Service Account)


This guide will help you set up Google Drive API access for automated operation without user interaction.

## Prerequisites

- Python 3.7 or higher
- Google account with Drive access
- Google Cloud Console access

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Google Drive API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

## Step 3: Create Service Account (for automated access)

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service account"
3. Fill in the service account details:
   - Name: "Drive HTML Reader Service"
   - Description: "Service account for automated Drive access"
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"
6. Click on the created service account
7. Go to the "Keys" tab
8. Click "Add Key" > "Create new key"
9. Choose "JSON" format
10. Download the JSON file and rename it to `service_account.json`
11. Place `service_account.json` in the same directory as your script

## Step 4: Share Drive Access with Service Account

**IMPORTANT**: The service account needs access to your Drive files.

1. Open your Google Drive
2. Create a folder for the files you want to access (optional, but recommended)
3. Right-click on the folder (or your entire Drive) and select "Share"
4. Add the service account email (found in the `service_account.json` file as `client_email`)
5. Give it "Viewer" permissions
6. Click "Send"

## Step 5: Install Dependencies

```bash
# Activate your conda environment first
conda activate vise3_py312

# Install required packages
pip install -r requirements.txt
```

## Step 6: Run the Script

```bash
python google_drive_reader.py
```

**No user interaction required!** The script will automatically authenticate using the service account and access your Drive files.

## Usage Examples

### Basic Usage
```python
from google_drive_reader import GoogleDriveReader

# Initialize reader
reader = GoogleDriveReader()

# Authenticate
if reader.authenticate():
    # Get all HTML files
    html_files = reader.get_html_files(max_files=20)
    
    # Process each file
    for file_data in html_files:
        print(f"File: {file_data['name']}")
        processed = reader.process_html_content(file_data['content'])
        print(f"Title: {processed['title']}")
```

### Search Specific Files
```python
# Search for files with specific names
files = reader.search_files("name contains 'report' and mimeType='text/html'")

# Search in specific folder
files = reader.search_files("'FOLDER_ID' in parents and mimeType='text/html'")
```

### Custom Processing
```python
# Get files and process them
html_files = reader.get_html_files(max_files=50)

for file_data in html_files:
    content = file_data['content']
    
    # Your custom processing here
    # Example: extract specific data, analyze content, etc.
    
    processed = reader.process_html_content(content)
    print(f"Processed: {file_data['name']}")
```

## Troubleshooting

### Authentication Issues
- Make sure `service_account.json` is in the correct directory
- Verify the service account has the correct permissions
- Check that the service account email is shared with your Drive/folders

### Permission Errors
- Verify that Google Drive API is enabled in your project
- Ensure the service account has been shared with the Drive files/folders you want to access
- Check that the service account has at least "Viewer" permissions

### File Not Found
- Ensure HTML files exist in your Drive
- Check that the service account has been shared with the files/folders
- Try different search queries
- Verify the service account email is correct in the sharing settings

## Security Notes

- Keep your `service_account.json` file secure and don't commit it to version control
- The service account key provides full access - treat it like a password
- Consider using environment variables for the service account file path
- Regularly rotate service account keys for security

## API Limits

- Google Drive API has rate limits (100 requests per 100 seconds per user)
- Large files may take time to download
- Consider implementing pagination for large result sets
