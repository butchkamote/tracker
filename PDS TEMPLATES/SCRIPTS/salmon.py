import os
import pandas as pd
from datetime import datetime, timedelta, date
import sys

# Force UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# =====================================
# ⚙️ AUTO DETECT DATE AND PATHS
# =====================================
today = datetime.today()
year = today.year
month_abbr = today.strftime('%b').upper()
month_full = today.strftime('%B').upper()
day = today.strftime('%d')
date_str = today.strftime('%Y_%m_%d')
month_day = f"{month_abbr.lower()}_{day}"

# =====================================
# 📁 UPDATED PATHS FOR WEB APP
# =====================================
# Use uploads folder instead of Windows paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up 2 levels to tracker root
uploads_folder = os.path.join(base_dir, "uploads")
output_folder = os.path.join(base_dir, "data", month_full, "OUTPUT_FOLDER", "PDS OUTPUT")

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

print(f"📂 Looking for SALMON files in uploads folder: {uploads_folder}")
print(f"📂 Output will be saved to: {output_folder}")

# --- UPDATED PATHS FOR WEB APP ---
# Source files come from uploads folder
source_dir = uploads_folder

# 🔹 Template path (using existing template in repo)
template_path = os.path.join(base_dir, "PDS TEMPLATES", "AUTO_TEMPLATES", "Template_Fintech.xlsx")

# 🔹 Output folder - create monthly subfolder
output_dir = os.path.join(output_folder, month_day)
os.makedirs(output_dir, exist_ok=True)

print(f"📅 Date: {today.strftime('%B %d, %Y')}")
print(f"📂 Looking for SALMON files in: {source_dir}")
print(f"📂 Output will be saved to: {output_dir}")

# =====================================
# 🧩 CHECK FOR UPLOADED FILES
# =====================================
if not os.path.exists(source_dir):
    os.makedirs(source_dir, exist_ok=True)
    print(f"⚠️ No uploads folder found - created it.")

# Check for SALMON files in uploads folder
salmon_files = [f for f in os.listdir(source_dir) if 'salmon' in f.lower() and f.endswith(('.xlsx', '.csv', '.xls'))]
if not salmon_files:
    print("⚠️ No SALMON files found yet inside uploads folder.")
    print(f"📥 Please upload your SALMON files via the web interface.")
    print("📁 Looking for files with 'salmon' in the filename.")
else:
    print(f"✅ Found {len(salmon_files)} SALMON file(s): {salmon_files}")

# =====================================
# 🔍 FIND SALMON FILES (MULTIPLE FILES SUPPORT)
# =====================================
salmon_files = []
for file in os.listdir(source_dir):
    if "salmon" in file.lower() and (file.endswith(".xlsx") or file.endswith(".csv")):
        salmon_files.append(os.path.join(source_dir, file))

if not salmon_files:
    print("⚠️ No SALMON files found yet inside ENDO folder.")
    print("📥 Please place your SALMON files inside:")
    print(f"   {source_dir}")
    exit()

print(f"✅ Found SALMON files: {salmon_files}")

# =====================================
# 🧾 READ TEMPLATE
# =====================================
if not os.path.exists(template_path):
    print(f"⚠️ Fintech template not found at:\n   {template_path}")
    print("📥 Please make sure Template_Fintech.xlsx is in the correct folder.")
    exit()

template_df = pd.read_excel(template_path)
template_cols = template_df.columns.tolist()

# =====================================
# 🧹 ENHANCED PHONE FORMATTING FUNCTION
# =====================================
def format_phone_salmon(phone_str):
    if pd.isna(phone_str) or phone_str in ['#N/A', 'N/A', '#N/A', '']:
        return ''
    
    # Convert to string and handle scientific notation
    phone_str = str(phone_str).strip()
    
    # Handle scientific notation (e.g., 6.39778E+11)
    if 'E+' in phone_str.upper() or 'e+' in phone_str:
        try:
            # Convert scientific notation to regular number
            phone_num = float(phone_str)
            phone_str = f"{phone_num:.0f}"
        except ValueError:
            pass
    
    # Handle Excel formula format (e.g., =63+639175544518)
    if phone_str.startswith('='):
        # Remove the = and try to evaluate simple addition
        formula = phone_str[1:]
        if '+' in formula:
            parts = formula.split('+')
            try:
                # Try to add the parts if they're numeric
                total = sum(float(part) for part in parts)
                phone_str = f"{total:.0f}"
            except ValueError:
                # If not numeric, just concatenate without the +
                phone_str = ''.join(parts)
        else:
            phone_str = formula
    
    # Remove .0 if present
    phone_str = phone_str.replace('.0', '').strip()
    
    # Skip if it's still not valid
    if phone_str in ['#N/A', 'N/A', '#N/A', '']:
        return ''
    
    # Extract only digits
    digits_only = ''.join(char for char in phone_str if char.isdigit())
    
    # Handle different phone number formats
    if digits_only.startswith('63') and len(digits_only) >= 12:
        # Remove country code 63 and add 0
        phone_str = '0' + digits_only[2:]
    elif digits_only.startswith('639') and len(digits_only) >= 12:
        # Remove 63 and keep 9
        phone_str = '0' + digits_only[2:]
    elif len(digits_only) >= 10:
        # For other cases, take last 10 digits and add 0
        phone_str = '0' + digits_only[-10:]
    else:
        return ''
    
    # Final validation - should be 11 digits starting with 0
    if len(phone_str) == 11 and phone_str.startswith('0'):
        return phone_str
    
    return ''

# =====================================
# 🧩 DATE PARSING FUNCTIONS
# =====================================
def parse_birthdate(date_str):
    if pd.isna(date_str):
        return pd.NaT
    try:
        if 'GMT' in str(date_str):
            date_part = str(date_str).split(' GMT')[0]
            parsed_date = pd.to_datetime(date_part, errors='coerce')
        else:
            parsed_date = pd.to_datetime(date_str, errors='coerce')
        
        # Remove timezone info if present
        if parsed_date is not pd.NaT and hasattr(parsed_date, 'tz') and parsed_date.tz is not None:
            parsed_date = parsed_date.tz_localize(None)
            
        return parsed_date
    except:
        return pd.NaT

def parse_due_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    try:
        if 'GMT' in str(date_str):
            date_part = str(date_str).split(' GMT')[0]
            parsed_date = pd.to_datetime(date_part, errors='coerce')
        else:
            parsed_date = pd.to_datetime(date_str, errors='coerce')
            
        # Remove timezone info if present
        if parsed_date is not pd.NaT and hasattr(parsed_date, 'tz') and parsed_date.tz is not None:
            parsed_date = parsed_date.tz_localize(None)
            
        return parsed_date
    except:
        return pd.NaT

def parse_last_payment_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    try:
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if parsed_date is not pd.NaT and hasattr(parsed_date, 'tz') and parsed_date.tz is not None:
            parsed_date = parsed_date.tz_localize(None)
        return parsed_date
    except:
        return pd.NaT

def split_name(name):
    if pd.isna(name) or str(name).strip() == '':
        return '', ''
    parts = str(name).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    else:
        return ' '.join(parts[:-1]), parts[-1]

# =====================================
# 🔁 PROCESS MULTIPLE SALMON FILES
# =====================================
all_outputs = []

for file in salmon_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read SALMON data with enhanced error handling
    if file.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        try:
            df = pd.read_csv(file, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file, encoding='latin1', low_memory=False)
            except Exception as e:
                print(f"❌ Failed to read {file}: {e}")
                continue

    # Create output DataFrame
    output_df = pd.DataFrame(columns=template_cols)

    # Enhanced mapping with your Excel mapping logic
    output_df['Loan_id'] = df.get('loan_number', pd.Series('', index=df.index)).astype(str)
    output_df['Debtor_id'] = df.get('loan_number', pd.Series('', index=df.index)).astype(str)
    output_df['Account_number'] = df.get('loan_number', pd.Series('', index=df.index)).astype(str)
    output_df['Debtors_reference_number'] = df.get('cif_id', None)
    output_df['Client_name'] = 'Salmon'
    output_df['Product_name'] = df.get('product_name', None)
    output_df['Goods_purchased'] = df.get('items', None)
    output_df['Date_of_contract'] = pd.to_datetime(df.get('loan_issue_date', None), errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df.get('initial_loan_amount', None)
    output_df['loan_term_days'] = None
    
    # Combine first and last name
    first_name = df.get('first_name', pd.Series('', index=df.index)).fillna('')
    last_name = df.get('last_name', pd.Series('', index=df.index)).fillna('')
    output_df['Debtor_name'] = first_name.astype(str) + ' ' + last_name.astype(str)
    output_df['Debtor_name'] = output_df['Debtor_name'].str.strip()
    
    output_df['Gender'] = None
    
    # Apply the parsing functions to the correct columns
    output_df['Debtor_birthdate'] = df.get('birth_date', pd.Series(pd.NaT, index=df.index)).apply(parse_birthdate)
    output_df['Address'] = df.get('living_address', None)
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = df.get('company_name', None)
    output_df['Salary'] = None
    output_df['Position'] = None
    output_df['email'] = df.get('email', None)
    output_df['Due_date'] = df.get('next_due_date', pd.Series(pd.NaT, index=df.index)).apply(parse_due_date)
    output_df['DPD'] = df.get('overdue_days', None)
    output_df['Current_DPD'] = df.get('overdue_days', None)
    output_df['Last_payment_date'] = df.get('last_payment_date', pd.Series(pd.NaT, index=df.index)).apply(parse_last_payment_date)
    output_df['Last_payment_amount'] = df.get('last_payment_amount', None)
    output_df['Principal_debt'] = df.get('initial_loan_amount', None)
    output_df['Outstanding_balance'] = df.get('outstanding_balance', None)
    output_df['Amount_with_discount'] = None
    output_df['Minimum_payment_amount'] = df.get('min_amount', None)

    # Enhanced phone formatting using your special function
    output_df['Mobile_phone'] = df.get('main_phone_number', pd.Series('', index=df.index)).apply(format_phone_salmon)
    output_df['Home_phone'] = None
    output_df['Office_phone'] = df.get('Windows 11Pro_phone_number', pd.Series('', index=df.index)).apply(format_phone_salmon)
    output_df['Emergency_contact'] = df.get('contact_person_phone_number', pd.Series('', index=df.index)).apply(format_phone_salmon)
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None

    # Set endorsement and pullout dates - ensure timezone-naive
    output_df['Endorsement_date'] = pd.Timestamp.today().normalize()
    output_df['Pull_out_date'] = output_df['Endorsement_date'] + pd.to_timedelta(30, unit='d')
    output_df['Segment'] = None

    # Name fields
    output_df['first_name'] = df.get('first_name', None)
    output_df['last_name'] = df.get('last_name', None)

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_SALMON_{date_str}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)
    print(f"✅ Combined SALMON file saved: {output_path}")
    print("✅ You can now upload this file to the PDS portal.")
else:
    print("❌ No files were processed successfully.")

# Add to each script (talacare.py, salmon.py, etc.)
if __name__ == '__main__':
    try:
        # Your existing script code
        print("✅ Script completed successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)