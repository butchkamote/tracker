# PDS Tracker - Web Upload System

## 📁 New Upload System for Render Hosting

Since the app is now hosted on Render (cloud), it can't access your local Windows folders. We've implemented a new upload system:

### How it works:

1. **Upload Files**: Use the web interface to upload your Excel/CSV files
2. **Files Storage**: All uploaded files go to the `uploads/` folder
3. **Run Scripts**: Scripts now look for files in the uploads folder instead of local directories
4. **Output**: Processed files are saved to `data/MONTH/OUTPUT_FOLDER/PDS OUTPUT/`

### For PDS Maker:

- **Before**: Files were read from `C:\Users\...\ENDO_FILE_MAYA\ENDO_2025OCT22\`
- **Now**: Files are read from the `uploads/` folder accessible via web upload

### File Naming:

Scripts look for files containing these keywords in the filename:
- **SALMON**: files with "salmon" in the name
- **HONEYLOAN**: files with "honeyloan", "honey_loan", or "honey loan" in the name
- **TALA**: files with "tala" in the name
- **etc.**

### Benefits:

- ✅ Works with cloud hosting (Render)
- ✅ Team members can access from anywhere
- ✅ No need for local folder setup
- ✅ Web-based file management
- ✅ Automatic duplicate handling

### Usage:

1. Go to PDS Maker page
2. Upload your files using the upload button
3. Run the corresponding script
4. Download processed files from the output