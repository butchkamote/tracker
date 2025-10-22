import os
import shutil
import glob
from datetime import datetime, timedelta
from flask import flash
import pandas as pd

class FileTransferManager:
    """Handles all file transfer operations for the dashboard"""
    
    def __init__(self):
        self.base_paths = {
            'ssth_yama_crm': r'C:\DA_PROCESS\ssth_yama\FILE\CRM',
            'ssth_yama_ptp': r'C:\DA_PROCESS\ssth_yama\FILE\PTP',
            'away_ptps': r'C:\Users\Windows 11Pro\OneDrive\DA_PROCESS\OCTOBER\AWAY\PTPs',
            'email_folder': r'C:\DA_PROCESS\ssth_yama\FILE\EMAIL_FOLDER',
            'endorsement': r'C:\DA_PROCESS\ssth_yama\FILE\ENDORSEMENT',
            # Updated: Two payment file destinations
            'payment_file_1': r'C:\DA_PROCESS\ssth_yama\FILE\PAYMENT_FILE',
            'payment_file_2': r'C:\DA_PROCESS\ssth_yama\PAYMENT_FILE',
            'endo_maya': r'C:\DA_PROCESS\ENDO_FILE_MAYA',
            'home_kvb': r'C:\Users\Windows 11Pro\OneDrive\DA_PROCESS\OCTOBER\HOME_KVB'
        }
        self.digital_sources = {
            'rea': r"Y:\DIGITAL\AGENT_REA\AGENT_REA.xlsx",
            'gina': r'Y:\DIGITAL\AGENT_GINA\Agent_Gina_Reyes October.xlsx',
            'mark': r'Y:\DIGITAL\AGENT_MARK JULIUS\AGENT_MARK_JULIUS.xlsx'
        }
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create directories if they don't exist"""
        for path in self.base_paths.values():
            os.makedirs(path, exist_ok=True)
    
    def upload_ptp_crm_files(self, ptp_file_path, crm_file_path):
        """
        Tile 1: Upload PTP & CRM files
        """
        try:
            results = {'status': 'success', 'messages': [], 'files_copied': []}
            
            # Copy PTP file to multiple locations
            if ptp_file_path and os.path.exists(ptp_file_path):
                ptp_filename = os.path.basename(ptp_file_path)
                
                # Copy to ssth_yama PTP folder
                ptp_dest1 = os.path.join(self.base_paths['ssth_yama_ptp'], ptp_filename)
                shutil.copy2(ptp_file_path, ptp_dest1)
                results['files_copied'].append(f"PTP -> {ptp_dest1}")
                
                # Copy to AWAY PTPs folder
                ptp_dest2 = os.path.join(self.base_paths['away_ptps'], ptp_filename)
                shutil.copy2(ptp_file_path, ptp_dest2)
                results['files_copied'].append(f"PTP -> {ptp_dest2}")
                
                results['messages'].append(f"✅ PTP file copied to 2 locations")
            else:
                results['messages'].append("❌ PTP file not found or invalid path")
                results['status'] = 'partial'
            
            # Copy CRM file
            if crm_file_path and os.path.exists(crm_file_path):
                crm_filename = os.path.basename(crm_file_path)
                crm_dest = os.path.join(self.base_paths['ssth_yama_crm'], crm_filename)
                shutil.copy2(crm_file_path, crm_dest)
                results['files_copied'].append(f"CRM -> {crm_dest}")
                results['messages'].append(f"✅ CRM file copied successfully")
            else:
                results['messages'].append("❌ CRM file not found or invalid path")
                results['status'] = 'partial'
            
            # Verify PTP naming convention
            yesterday = datetime.now() - timedelta(days=1)
            expected_ptp_pattern = f"PTP_{yesterday.strftime('%B%d').upper()}.csv"
            
            verification_results = self._verify_ptp_files(expected_ptp_pattern)
            results['messages'].extend(verification_results)
            
            return results
            
        except Exception as e:
            return {'status': 'error', 'message': f"Error in PTP/CRM upload: {str(e)}"}
    
    def _verify_ptp_files(self, expected_pattern):
        """Verify PTP files exist with correct naming"""
        messages = []
        folders_to_check = [
            self.base_paths['ssth_yama_ptp'],
            self.base_paths['away_ptps']
        ]
        
        for folder in folders_to_check:
            matching_files = glob.glob(os.path.join(folder, expected_pattern))
            if matching_files:
                messages.append(f"✅ Found {expected_pattern} in {folder}")
            else:
                messages.append(f"⚠️ {expected_pattern} not found in {folder}")
        
        return messages
    
    def collect_digital_files(self):
        """
        Tile 2: Collect DIGITAL Excel Files
        """
        try:
            results = {'status': 'success', 'messages': [], 'files_copied': []}
            
            for agent, source_path in self.digital_sources.items():
                if os.path.exists(source_path):
                    filename = os.path.basename(source_path)
                    dest_path = os.path.join(self.base_paths['email_folder'], filename)
                    
                    shutil.copy2(source_path, dest_path)
                    results['files_copied'].append(f"{agent.upper()} -> {dest_path}")
                    results['messages'].append(f"✅ {agent.upper()} file copied successfully")
                else:
                    results['messages'].append(f"❌ {agent.upper()} file not found: {source_path}")
                    results['status'] = 'partial'
            
            return results
            
        except Exception as e:
            return {'status': 'error', 'message': f"Error collecting digital files: {str(e)}"}
    
    def collect_endo_files(self, month_abbr):
        """
        Tile 3: Collect ENDO files (dynamic by date + month input)
        """
        try:
            results = {'status': 'success', 'messages': [], 'files_copied': []}
            
            # Construct folder name: ENDO_YYYY[MMM][DD] - using YESTERDAY's date
            yesterday = datetime.now() - timedelta(days=1)  # Get yesterday's date
            
            if month_abbr:
                # Use provided month with yesterday's day
                folder_name = f"ENDO_{yesterday.year}{month_abbr.upper()}{yesterday.strftime('%d')}"
            else:
                # Use yesterday's month and day
                folder_name = f"ENDO_{yesterday.strftime('%Y%b%d').upper()}"
            
            endo_folder_path = os.path.join(self.base_paths['endo_maya'], folder_name)
            
            if not os.path.exists(endo_folder_path):
                return {'status': 'error', 'message': f"ENDO folder not found: {endo_folder_path}"}
            
            # File patterns to search for
            patterns = [
                'MAYA ENDORSEMENT*MPL*',
                'MAYA ENDORSEMENT*MCC*', 
                'MAYA ENDORSEMENT*MEC*',
                'MAYA ENDORSEMENT*mayacredit*'
            ]
            
            files_found = 0
            for pattern in patterns:
                matching_files = glob.glob(os.path.join(endo_folder_path, pattern))
                
                for file_path in matching_files:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.base_paths['endorsement'], filename)
                    
                    shutil.copy2(file_path, dest_path)
                    results['files_copied'].append(f"{filename} -> ENDORSEMENT")
                    files_found += 1
            
            if files_found > 0:
                results['messages'].append(f"✅ Found and copied {files_found} ENDO files from {folder_name} (yesterday)")
            else:
                results['messages'].append(f"⚠️ No ENDO files found matching patterns in {folder_name} (yesterday)")
                results['status'] = 'partial'
            
            return results
            
        except Exception as e:
            return {'status': 'error', 'message': f"Error collecting ENDO files: {str(e)}"}
    
    def collect_home_kvb_files(self):
        """
        Tile 4: Collect HOME_KVB files - Copy to BOTH payment directories
        """
        try:
            results = {'status': 'success', 'messages': [], 'files_copied': []}
            
            # Files to collect from HOME_KVB
            target_files = [
                'CREDIT_OCT.xlsx',
                'MPL_OCT.xlsx', 
                'MCC_OCT.xlsx'
            ]
            
            # Both payment destinations
            payment_destinations = [
                self.base_paths['payment_file_1'],  # C:\DA_PROCESS\ssth_yama\FILE\PAYMENT_FILE
                self.base_paths['payment_file_2']   # C:\DA_PROCESS\ssth_yama\PAYMENT_FILE
            ]
            
            files_copied_count = 0
            
            for filename in target_files:   
                source_path = os.path.join(self.base_paths['home_kvb'], filename)
                
                if os.path.exists(source_path):
                    # Copy to both payment directories
                    for i, dest_dir in enumerate(payment_destinations, 1):
                        try:
                            dest_path = os.path.join(dest_dir, filename)
                            
                            # Copy and overwrite
                            shutil.copy2(source_path, dest_path)
                            results['files_copied'].append(f"{filename} -> PAYMENT_FILE_{i}")
                            
                        except Exception as copy_error:
                            results['messages'].append(f"❌ Error copying {filename} to PAYMENT_FILE_{i}: {copy_error}")
                            results['status'] = 'partial'
                    
                    results['messages'].append(f"✅ {filename} copied to both payment directories")
                    files_copied_count += 1
                    
                else:
                    results['messages'].append(f"❌ {filename} not found in HOME_KVB")
                    
                    # Debug: Show what files are actually in HOME_KVB
                    if os.path.exists(self.base_paths['home_kvb']):
                        try:
                            actual_files = os.listdir(self.base_paths['home_kvb'])
                            results['messages'].append(f"📁 Files in HOME_KVB: {actual_files}")
                        except:
                            pass
                    
                    results['status'] = 'partial'
            
            # Summary
            if files_copied_count > 0:
                results['messages'].append(f"🎉 Successfully copied {files_copied_count}/{len(target_files)} files to both payment directories")
            else:
                results['status'] = 'error'
                results['messages'].append("❌ No files were copied to payment directories")
            
            return results
            
        except Exception as e:
            return {'status': 'error', 'message': f"Error collecting HOME_KVB files: {str(e)}"}
    
    def get_folder_status(self):
        """Get status of all target folders"""
        status = {}
        for name, path in self.base_paths.items():
            status[name] = {
                'exists': os.path.exists(path),
                'files_count': len(os.listdir(path)) if os.path.exists(path) else 0,
                'path': path
            }
        return status
    
    def cleanup_old_files(self, days_old=7):
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_files = []
            
            for folder_name, folder_path in self.base_paths.items():
                if os.path.exists(folder_path):
                    for filename in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, filename)
                        if os.path.isfile(file_path):
                            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mod_time < cutoff_date:
                                os.remove(file_path)
                                cleaned_files.append(f"{folder_name}/{filename}")
            
            return {
                'status': 'success',
                'message': f"Cleaned {len(cleaned_files)} old files",
                'files': cleaned_files
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f"Error during cleanup: {str(e)}"}

# Create global instance
file_manager = FileTransferManager()

# Helper functions for Flask routes
def handle_ptp_crm_upload(ptp_file_path, crm_file_path):
    """Handle PTP & CRM file upload"""
    return file_manager.upload_ptp_crm_files(ptp_file_path, crm_file_path)

def handle_digital_collection():
    """Handle digital files collection"""
    return file_manager.collect_digital_files()

def handle_endo_collection(month_abbr):
    """Handle ENDO files collection"""
    return file_manager.collect_endo_files(month_abbr)

def handle_home_kvb_collection():
    """Handle HOME_KVB files collection"""
    return file_manager.collect_home_kvb_files()

def get_transfer_status():
    """Get overall transfer status"""
    return file_manager.get_folder_status()

def cleanup_transfer_files(days=7):
    """Cleanup old transfer files"""
    return file_manager.cleanup_old_files(days)