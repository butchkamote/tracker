import os
import pandas as pd
from datetime import datetime, timedelta, date

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

# --- MAIN PATHS ---
base_dir = r"C:\Users\Windows 11Pro\OneDrive\DA_PROCESS"
month_dir = os.path.join(base_dir, month_full)
endo_base = os.path.join(month_dir, "ENDO_FILE_MAYA")

# 🔹 Dynamic ENDO folder (e.g., ENDO_2025OCT14)
endo_folder = f"ENDO_{year}{month_abbr}{day}"
source_dir = os.path.join(endo_base, endo_folder)

# 🔹 Template & Output folders
template_path = os.path.join(endo_base, "PDS TEMPLATES", "AUTO_TEMPLATES", "Template_Fintech.xlsx")
output_dir = os.path.join(month_dir, "OUTPUT_FOLDER\PDS OUTPUT", month_day)
os.makedirs(output_dir, exist_ok=True)

print(f"📅 Date: {today.strftime('%B %d, %Y')}")
print(f"📂 Expected ENDO folder: {source_dir}")

# =====================================
# 🧩 CHECK OR CREATE ENDO FOLDER
# =====================================
if not os.path.exists(source_dir):
    os.makedirs(source_dir, exist_ok=True)
    print(f"⚠️ No ENDO folder found — created {endo_folder}.")
    print("📥 Please place your PITACASH files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND PITACASH FILES (MULTIPLE FILES SUPPORT)
# =====================================
pitacash_files = []
for file in os.listdir(source_dir):
    if "pitacash" in file.lower() or "pita_cash" in file.lower() or "pita cash" in file.lower():
        if file.endswith(".xlsx") or file.endswith(".csv"):
            pitacash_files.append(os.path.join(source_dir, file))

if not pitacash_files:
    print("⚠️ No PITACASH files found yet inside ENDO folder.")
    print("📥 Please place your PITACASH files inside:")
    print(f"   {source_dir}")
    exit()

print(f"✅ Found PITACASH files: {pitacash_files}")

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
# 🧹 PHONE FORMATTING FUNCTION
# =====================================
def format_phone_63_to_0(phone_str):
    if pd.isna(phone_str) or phone_str in ['#N/A', 'N/A', '#N/A', '']:
        return ''
    
    phone_str = str(phone_str).replace('.0', '').strip()
    
    if phone_str.startswith('63') and len(phone_str) > 2:
        phone_str = '0' + phone_str[2:]
    
    return phone_str

# =====================================
# 🧩 HELPER FUNCTIONS
# =====================================
def split_acct_name(acct_name):
    if pd.isna(acct_name) or str(acct_name).strip() == '':
        return '', ''
    
    name_parts = str(acct_name).strip().split()
    if len(name_parts) == 0:
        return '', ''
    elif len(name_parts) == 1:
        return name_parts[0], ''
    else:
        first_name = name_parts[0]
        last_name = name_parts[-1]
        return first_name, last_name

def split_name(name):
    if pd.isna(name) or str(name).strip() == '':
        return '', ''
    parts = str(name).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    else:
        return ' '.join(parts[:-1]), parts[-1]

# =====================================
# 🔁 PROCESS MULTIPLE PITACASH FILES
# =====================================
all_outputs = []

for file in pitacash_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read PITACASH data with enhanced error handling
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

    # Enhanced mapping with your PITACASH mapping logic
    output_df['Loan_id'] = df.get('Loan No', pd.Series('', index=df.index)).astype(str)
    output_df['Debtor_id'] = df.get('Loan No', pd.Series('', index=df.index)).astype(str)
    output_df['Account_number'] = df.get('LifeTimeID', pd.Series('', index=df.index)).astype(str)
    output_df['Debtors_reference_number'] = df.get('LifeTimeID', None)
    output_df['Client_name'] = 'PITACASH'
    output_df['Product_name'] = df.get('Product type', None)
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df.get('Disbursement Date', None), errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df.get('Loan Amount', None)
    output_df['loan_term_days'] = df.get('Loan Term', None)
    output_df['Debtor_name'] = df.get('Acct Name', None)
    output_df['Gender'] = None
    output_df['Debtor_birthdate'] = None
    output_df['Address'] = df.get('Address', None)
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = None
    output_df['Salary'] = None
    output_df['Position'] = df.get('Job Title', None)
    output_df['email'] = df.get('Email Address', None)
    output_df['Due_date'] = pd.to_datetime(df.get('Due Date', None), errors='coerce')
    output_df['DPD'] = df.get('DPD', None)
    output_df['Current_DPD'] = df.get('DPD', None)
    output_df['Last_payment_date'] = pd.to_datetime(df.get('Last Payment Date', None), errors='coerce')
    output_df['Last_payment_amount'] = df.get('Last Payment Amount', None)
    output_df['Principal_debt'] = df.get('Principal Oustanding Balance', None)
    output_df['Outstanding_balance'] = df.get('Total Outstanding Balance', None)
    output_df['Amount_with_discount'] = df.get('Total Discounted Amount for Loan Closure', None)
    output_df['Minimum_payment_amount'] = df.get('NPGF', None)

    # Phone formatting using your custom function
    output_df['Mobile_phone'] = df.get('Contact No', pd.Series('', index=df.index)).apply(format_phone_63_to_0)
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    output_df['Emergency_contact'] = df.get('Other Contact Number 1', pd.Series('', index=df.index)).apply(format_phone_63_to_0)
    output_df['Alternative_number_1'] = df.get('Other Contact Number 2', pd.Series('', index=df.index)).apply(format_phone_63_to_0)
    output_df['Alternative_number_2'] = df.get('Other Contact Number 3', pd.Series('', index=df.index)).apply(format_phone_63_to_0)
    output_df['Alternative_number_3'] = None

    # Date assignments from your mapping
    output_df['Endorsement_date'] = pd.to_datetime(df.get('Endorsement Date', None), errors='coerce')
    output_df['Pull_out_date'] = output_df['Endorsement_date'] + pd.to_timedelta(90, unit='d')
    output_df['Segment'] = None

    # Name splitting using your split_acct_name function
    name_split = df.get('Acct Name', pd.Series('', index=df.index)).apply(split_acct_name)
    output_df['first_name'] = [x[0] for x in name_split]
    output_df['last_name'] = [x[1] for x in name_split]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_PITACASH_{date_str}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)
    print(f"✅ Combined PITACASH file saved: {output_path}")
    print("✅ You can now upload this file to the PDS portal.")
else:
    print("❌ No files were processed successfully.")