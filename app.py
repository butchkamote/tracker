from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime, date
import threading
import schedule
import time
import subprocess
import sys
import traceback
import base64
import pandas as pd

from loxon import (
    handle_ptp_crm_upload,
    handle_digital_collection,
    handle_endo_collection,
    handle_home_kvb_collection,
    get_transfer_status,
    cleanup_transfer_files
)
app = Flask(__name__)

# Data storage
PROGRESS_FILE = 'progress_data.json'

# Updated Task categories based on your requirements
TASK_CATEGORIES = {
    'ENDORSEMENT_MAYA': ['MCC', 'MPL', 'MEC'],
    'ENDORSEMENT_OLA': ['SKYRO', 'OLP', 'PR', 'KVIKU', 'HONEYLOAN', 'PITACASH', 'TALA', 'TALACARE', 'SALMON', 'NETBANK', 'AKULAKU'],
    'LOXON': ['MAYA'],  # Only 1 MAYA (covers all 3: MEC, MPL, MCC)
    'DCA_MAYA': ['MEC', 'MPL', 'MCC'],  # 3 DCA tasks
    'PAYMENTS_MAYA': ['MCC', 'MPL', 'MEC'],
    'PAYMENTS_OLA': ['SKYRO', 'OLP', 'PR', 'KVIKU', 'HONEYLOAN', 'PITACASH', 'TALA', 'TALACARE', 'SALMON', 'NETBANK', 'AKULAKU']
}

STATUSES = ['PENDING', 'DOWNLOADED', 'PROCESSED', 'UPLOADED', 'N/A']
STATUS_COLORS = {
    'PENDING': '#ffc107',
    'DOWNLOADED': '#17a2b8', 
    'PROCESSED': '#fd7e14',
    'UPLOADED': '#28a745',
    'N/A': '#6c757d'  # Gray color for N/A
}

# Payment reminder times
PAYMENT_REMINDERS = ['12:00', '20:00']  # 12 noon and 8pm

def load_progress():
    """Load progress data from JSON file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Initialize default data
    today = date.today().strftime('%Y-%m-%d')
    data = {
        'last_updated': today,
        'tasks': {}
    }
    
    for category, items in TASK_CATEGORIES.items():
        for item in items:
            data['tasks'][f"{category}_{item}"] = {
                'category': category,
                'name': item,
                'status': 'PENDING',
                'assigned_to': '',
                'last_updated': today,
                'notes': ''
            }
    
    save_progress(data)
    return data

def save_progress(data):
    """Save progress data to JSON file"""
    data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_payment_reminder():
    """Send payment reminder notification"""
    data = load_progress()
    
    # Check PAYMENTS tasks that are not UPLOADED
    pending_payments = []
    for task_key, task in data['tasks'].items():
        if 'PAYMENTS' in task['category'] and task['status'] != 'UPLOADED':
            pending_payments.append(f"{task['category']} - {task['name']} ({task['status']})")
    
    if pending_payments:
        current_time = datetime.now().strftime('%H:%M')
        print(f"\n🚨 PAYMENT REMINDER - {current_time}")
        print("=" * 50)
        print("⚠️  Pending payment tasks:")
        for payment in pending_payments:
            print(f"   • {payment}")
        print("=" * 50)
        # You can add more notification methods here (email, Telegram, etc.)

# Schedule payment reminders
schedule.every().day.at("12:00").do(send_payment_reminder)
schedule.every().day.at("20:00").do(send_payment_reminder)

def run_scheduler():
    """Run the scheduler in background"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

@app.route('/')
def dashboard():
    """Main dashboard page"""
    data = load_progress()
    return render_template('dashboard.html', 
                         data=data, 
                         categories=TASK_CATEGORIES,
                         statuses=STATUSES,
                         colors=STATUS_COLORS,
                         reminders=PAYMENT_REMINDERS)

@app.route('/update_task', methods=['POST'])
def update_task():
    """Update task status"""
    task_key = request.json.get('task_key')
    new_status = request.json.get('status')
    assigned_to = request.json.get('assigned_to', '')
    notes = request.json.get('notes', '')
    
    data = load_progress()
    if task_key in data['tasks']:
        data['tasks'][task_key]['status'] = new_status
        data['tasks'][task_key]['assigned_to'] = assigned_to
        data['tasks'][task_key]['notes'] = notes
        data['tasks'][task_key]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_progress(data)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/reset_all')
def reset_all():
    """Reset all tasks to PENDING"""
    data = load_progress()
    for task_key in data['tasks']:
        data['tasks'][task_key]['status'] = 'PENDING'
        data['tasks'][task_key]['assigned_to'] = ''
        data['tasks'][task_key]['notes'] = ''
    save_progress(data)
    return redirect(url_for('dashboard'))

@app.route('/manual_reminder')
def manual_reminder():
    """Manually trigger payment reminder"""
    send_payment_reminder()
    return jsonify({'success': True, 'message': 'Payment reminder sent!'})

def setup_static_folders():
    """Create static directories if they don't exist"""
    static_dirs = ['static', 'static/css', 'static/js', 'templates']
    for dir_name in static_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

def open_browser():
    """Open browser after a delay - disabled for production deployment"""
    # Don't open browser in production/Render environment
    pass

# PDS Campaigns from your monthly flask app
CAMPAIGNS = [
    {'name': 'TALACARE', 'script': 'SCRIPTS/talacare.py', 'color': '#ff6b35', 'icon': '🏥'},
    {'name': 'SALMON', 'script': 'SCRIPTS/salmon.py', 'color': '#00d4ff', 'icon': '🐟'},
    {'name': 'SKYRO', 'script': 'SCRIPTS/skyro.py', 'color': '#39ff14', 'icon': '🌤️'},
    {'name': 'OLP', 'script': 'SCRIPTS/olp.py', 'color': '#ff073a', 'icon': '💼'},
    {'name': 'PR', 'script': 'SCRIPTS/pr.py', 'color': '#ffff00', 'icon': '💰'},
    {'name': 'KVIKU', 'script': 'SCRIPTS/kviku.py', 'color': '#00ff80', 'icon': '🏦'},
    {'name': 'HONEYLOAN', 'script': 'SCRIPTS/honeyloan.py', 'color': '#ffa500', 'icon': '🍯'},
    {'name': 'TALA', 'script': 'SCRIPTS/tala.py', 'color': '#ff1493', 'icon': '🌱'},
    {'name': 'PITACASH', 'script': 'SCRIPTS/pitacash.py', 'color': '#00ffff', 'icon': '💳'}
]

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_endo_folder():
    """Check uploads folder for uploaded files"""
    today = datetime.today()
    year = today.year
    month_abbr = today.strftime('%b').upper()
    day = today.strftime('%d')
    
    endo_folder = f"ENDO_{year}{month_abbr}{day}"
    # Use uploads folder in project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads")
    
    # Create uploads directory if it doesn't exist
    os.makedirs(uploads_dir, exist_ok=True)
    
    return {
        'exists': True,  # Always true since we create it
        'folder_name': endo_folder,
        'full_path': uploads_dir,
        'date': today.strftime('%B %d, %Y')
    }

# Add PDS Maker route
@app.route('/pds_maker')
def pds_maker():
    endo_status = check_endo_folder()
    return render_template('pds_maker.html', 
                         campaigns=CAMPAIGNS, 
                         endo_status=endo_status)


@app.route('/pds_upload/<campaign>', methods=['POST'])
def pds_upload(campaign):
    """Handle file upload from PDS Maker UI. Save file using original filename (no campaign prefix).

    Reject upload if the destination file already exists.
    """
    try:
        # Ensure file present
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

        # Determine ENDO folder
        endo_status = check_endo_folder()
        dest_folder = endo_status.get('full_path')

        if not dest_folder or not os.path.exists(dest_folder):
            return jsonify({'status': 'error', 'message': f'ENDO folder not found: {dest_folder}'}), 400

        # Use secure filename and DO NOT prefix with campaign name
        filename = secure_filename(file.filename)
        dest_path = os.path.join(dest_folder, filename)

        # If file exists, reject as requested
        if os.path.exists(dest_path):
            return jsonify({'status': 'error', 'message': 'File with same name already exists'}), 409

        # Save file
        file.save(dest_path)

        return jsonify({'status': 'success', 'message': f'Uploaded as {filename}', 'path': dest_path})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/run/<campaign_name>')
def run_script(campaign_name):
    campaign = next((c for c in CAMPAIGNS if c['name'] == campaign_name), None)
    if not campaign:
        return jsonify({'status': 'error', 'message': 'Campaign not found'})

    # Use relative path from project root for scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "PDS TEMPLATES", "SCRIPTS")
    script_path = os.path.join(scripts_dir, f"{campaign_name.lower()}.py")
    
    # Create PDS OUTPUT folder
    today = datetime.today()
    month_full = today.strftime('%B').upper()
    pds_output_dir = os.path.join(base_dir, "data", month_full, "OUTPUT_FOLDER", "PDS OUTPUT")
    
    try:
        # Check if script file exists
        if not os.path.exists(script_path):
            return jsonify({
                'status': 'error',
                'message': f'Script not found: {script_path}',
                'debug_info': f'Looking for: {script_path}'
            })
        
        # Create PDS OUTPUT directory if it doesn't exist
        os.makedirs(pds_output_dir, exist_ok=True)
        
        # Set environment variables for the script
        env = os.environ.copy()
        env['PYTHONPATH'] = scripts_dir
        
        result = subprocess.run(
            [sys.executable, script_path], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            cwd=scripts_dir,  # Set working directory to SCRIPTS folder
            env=env  # Pass environment with PYTHONPATH
        )
        
        # Generate timestamp for the log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"{campaign_name}_{timestamp}.log"
        log_path = os.path.join(pds_output_dir, log_filename)
        
        # Save output to log file in PDS OUTPUT folder
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"Campaign: {campaign_name}\n")
            log_file.write(f"Script: {script_path}\n")
            log_file.write(f"Working Directory: {scripts_dir}\n")
            log_file.write(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Return Code: {result.returncode}\n")
            log_file.write("=" * 50 + "\n")
            log_file.write("STDOUT:\n")
            log_file.write(result.stdout if result.stdout else "(No output)")
            log_file.write("\n" + "=" * 50 + "\n")
            log_file.write("STDERR:\n")
            log_file.write(result.stderr if result.stderr else "(No errors)")
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'output': result.stdout or '(Script completed with no console output)',
                'message': f'{campaign_name} script completed successfully',
                'log_file': log_path,
                'output_folder': pds_output_dir,
                'debug_info': f'Script executed: {script_path}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Script execution failed (Return Code: {result.returncode})',
                'error': result.stderr,
                'output': result.stdout,
                'log_file': log_path,
                'output_folder': pds_output_dir,
                'debug_info': f'Script path: {script_path}, Working dir: {scripts_dir}'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error running script: {str(e)}',
            'script_path': script_path,
            'debug_info': f'Exception occurred while executing {script_path}'
        })

@app.route('/open_output_folder')
def open_output_folder():
    try:
        today = datetime.today()
        month_full = today.strftime('%B').upper()
        
        # Use relative path from project root
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pds_output_dir = os.path.join(base_dir, "data", month_full, "OUTPUT_FOLDER", "PDS OUTPUT")
        
        if os.path.exists(pds_output_dir):
            # For web app, just return success - no need to open folders on server
            return jsonify({'status': 'success', 'message': 'PDS Output folder exists', 'path': pds_output_dir})
        else:
            os.makedirs(pds_output_dir, exist_ok=True)
            return jsonify({'status': 'success', 'message': 'PDS Output folder created', 'path': pds_output_dir})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/list_uploads')
def list_uploads():
    """List all files in the uploads folder"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(base_dir, "uploads")
        
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
            return jsonify({'status': 'success', 'files': [], 'message': 'Uploads folder created'})
        
        files = []
        for filename in os.listdir(uploads_dir):
            if os.path.isfile(os.path.join(uploads_dir, filename)):
                file_path = os.path.join(uploads_dir, filename)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                
                files.append({
                    'name': filename,
                    'size': f"{file_size / 1024:.1f} KB",
                    'modified': file_modified
                })
        
        return jsonify({'status': 'success', 'files': files, 'total': len(files)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/upload_to_folder', methods=['POST'])
def upload_to_folder():
    """Upload files directly to the uploads folder"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': 'File type not allowed. Use CSV, XLS, or XLSX files.'}), 400
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        uploads_dir = os.path.join(base_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(uploads_dir, filename)
        
        # Handle duplicate files
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            new_filename = f"{base_name}({counter}){ext}"
            file_path = os.path.join(uploads_dir, new_filename)
            filename = new_filename
            counter += 1
        
        file.save(file_path)
        
        return jsonify({
            'status': 'success',
            'message': f'File uploaded successfully: {filename}',
            'filename': filename,
            'path': file_path
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/create_endo_folder')
def create_endo_folder():
    endo_status = check_endo_folder()
    try:
        # Uploads folder is always available
        return jsonify({
            'status': 'success',
            'message': 'Uploads folder ready',
            'path': endo_status['full_path']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })
        
# Add global variable for LOXON progress tracking
loxon_progress = {
    'upload_sql': False,
    'microsoft_sql': False,
    'inventory': False,
    'loxon_process': False
}

@app.route('/loxon/upload_sql_done', methods=['POST'])
def loxon_upload_sql_done():
    """Mark Upload SQL as completed"""
    try:
        global loxon_progress
        loxon_progress['upload_sql'] = True
        
        return jsonify({
            'status': 'success',
            'message': 'Upload SQL marked as completed',
            'progress': loxon_progress
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/run_microsoft_sql', methods=['POST'])
def loxon_run_microsoft_sql():
    """Execute Microsoft SQL operations"""
    try:
        global loxon_progress
        
        # Check prerequisite
        if not loxon_progress['upload_sql']:
            return jsonify({
                'status': 'error', 
                'message': 'Prerequisites not met: Upload SQL must be completed first'
            }), 400
        
        # Placeholder for actual SQL operations
        # You can add your SQL script execution here
        base_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run([sys.executable, os.path.join(base_dir, 'PDS TEMPLATES', 'SCRIPTS', 'microsoft_sql.py')], 
                              capture_output=True, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            loxon_progress['microsoft_sql'] = True
            return jsonify({
                'status': 'success',
                'message': 'Microsoft SQL operations completed successfully',
                'messages': ['✅ SQL Server operations executed'],
                'progress': loxon_progress
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Microsoft SQL failed: {result.stderr}'
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/run_inventory', methods=['POST'])
def loxon_run_inventory():
    """Generate inventory reports"""
    try:
        global loxon_progress
        
        # Check prerequisites
        if not loxon_progress['upload_sql'] or not loxon_progress['microsoft_sql']:
            return jsonify({
                'status': 'error', 
                'message': 'Prerequisites not met: Upload SQL and Microsoft SQL must be completed first'
            }), 400
        
        # Placeholder for inventory script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run([sys.executable, os.path.join(base_dir, 'PDS TEMPLATES', 'SCRIPTS', 'inventory.py')], 
                              capture_output=True, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            loxon_progress['inventory'] = True
            return jsonify({
                'status': 'success',
                'message': 'Inventory report generated successfully',
                'messages': ['✅ Inventory report created'],
                'files': ['inventory_report.xlsx'],
                'progress': loxon_progress
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Inventory generation failed: {result.stderr}'
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/run_loxon_process', methods=['POST'])
def loxon_run_loxon_process():
    """Execute main LOXON processing workflow"""
    try:
        global loxon_progress
        
        # Check all prerequisites
        if not all([loxon_progress['upload_sql'], loxon_progress['microsoft_sql'], loxon_progress['inventory']]):
            return jsonify({
                'status': 'error', 
                'message': 'Prerequisites not met: Upload SQL, Microsoft SQL, and Inventory must be completed first'
            }), 400
        
        # Placeholder for main LOXON process
        base_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run([sys.executable, os.path.join(base_dir, 'PDS TEMPLATES', 'SCRIPTS', 'loxon_process.py')], 
                              capture_output=True, text=True, cwd=base_dir)
        
        if result.returncode == 0:
            loxon_progress['loxon_process'] = True
            return jsonify({
                'status': 'success',
                'message': 'LOXON process completed successfully',
                'messages': ['✅ Main LOXON workflow executed', '✅ All processes completed'],
                'progress': loxon_progress
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'LOXON process failed: {result.stderr}'
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/reset_progress', methods=['POST'])
def loxon_reset_progress():
    """Reset all LOXON progress"""
    try:
        global loxon_progress
        loxon_progress = {
            'upload_sql': False,
            'microsoft_sql': False,
            'inventory': False,
            'loxon_process': False
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Progress reset successfully',
            'progress': loxon_progress
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/progress')
def loxon_get_progress():
    """Get current LOXON progress"""
    try:
        global loxon_progress
        return jsonify({
            'status': 'success',
            'progress': loxon_progress
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon')
def loxon_page():
    """LOXON File Transfer Dashboard"""
    global loxon_progress
    return render_template('loxon.html', progress=loxon_progress)

# Add missing file transfer routes (these are referenced in your loxon.js)
@app.route('/loxon/upload_ptp_crm', methods=['POST'])
def loxon_upload_ptp_crm():
    """Handle PTP & CRM file upload"""
    try:
        result = handle_ptp_crm_upload(request)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/collect_digital', methods=['POST'])
def loxon_collect_digital():
    """Collect DIGITAL Excel files"""
    try:
        result = handle_digital_collection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/collect_endo', methods=['POST'])
def loxon_collect_endo():
    """Collect ENDO files with month input"""
    try:
        month = request.json.get('month', '') if request.is_json else ''
        result = handle_endo_collection(month)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/collect_home_kvb', methods=['POST'])
def loxon_collect_home_kvb():
    """Collect HOME_KVB files"""
    try:
        result = handle_home_kvb_collection()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/loxon/status')
def loxon_status():
    """Get transfer status"""
    try:
        result = get_transfer_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/upload/<campaign_name>', methods=['POST'])
def upload_file(campaign_name):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
        
    if file and allowed_file(file.filename):
        # Get today's ENDO folder path
        endo_status = check_endo_folder()
        if not os.path.exists(endo_status['full_path']):
            os.makedirs(endo_status['full_path'], exist_ok=True)
            
        # Secure the filename WITHOUT campaign prefix
        original_filename = secure_filename(file.filename)
        
        # Handle duplicate files with (1), (2) numbering
        base_name, ext = os.path.splitext(original_filename)
        filename = original_filename
        counter = 1
        
        while os.path.exists(os.path.join(endo_status['full_path'], filename)):
            filename = f"{base_name}({counter}){ext}"
            counter += 1
        
        file_path = os.path.join(endo_status['full_path'], filename)
        
        try:
            file.save(file_path)
            return jsonify({
                'status': 'success',
                'message': f'File uploaded successfully: {filename}',
                'path': file_path
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error saving file: {str(e)}'
            })
    
    return jsonify({'status': 'error', 'message': 'Invalid file type'})

if __name__ == '__main__':
    setup_static_folders()
    
    print("🚀 Starting DA Process Progress Tracker...")
    print("📡 Server will be accessible at:")
    print("   Local: http://localhost:4000")
    print("\n👥 Share this with your team!")
    print("🔄 Auto-refreshes every 30 seconds")
    print("📊 Real-time progress tracking")
    print("⏰ Payment reminders at 12:00 PM & 8:00 PM")
    
    # Start scheduler in background
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Don't open browser in production
    # threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app - let Render handle the port
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port, debug=False)