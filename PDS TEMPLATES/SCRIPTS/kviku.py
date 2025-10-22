import os
import pandas as pd
from datetime import datetime, date, timedelta
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
    print("📥 Please place your KVIKU files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND KVIKU FILES (MULTIPLE FILES SUPPORT)
# =====================================
kviku_files = []
for file in os.listdir(source_dir):
    if "Loans_" in file and (file.endswith(".xlsx") or file.endswith(".csv")):
        kviku_files.append(os.path.join(source_dir, file))

if not kviku_files:
    print("⚠️ No KVIKU files found yet inside ENDO folder.")
    print("📥 Please place your KVIKU files (e.g., Loans_14_10_2025.xlsx) inside:")
    print(f"   {source_dir}")
    exit()

print(f"✅ Found KVIKU files: {kviku_files}")

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
def format_phone(series):
    # Replace leading country code 63 with 0, remove non-digits, ensure max 11 digits
    return (
        '0' + series.astype(str).str.replace(r'\.0$', '', regex=True)
        .str.replace(r'\D', '', regex=True).str[-10:]
    )

# =====================================
# 🧩 DEFINE HELPER FUNCTIONS
# =====================================
def pullkvi(row):
    """Calculate pull-out date logic"""
    if row['Endorsement_date'] + pd.to_timedelta(90, unit='D') <= datetime.today():
        return pd.to_datetime(date.today() + timedelta(days=1))
    else:
        return row['Endorsement_date'] + pd.to_timedelta(90, unit='D')

def split_name(name):
    if pd.isna(name) or str(name).strip() == '':
        return '', ''
    parts = str(name).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    else:
        return ' '.join(parts[:-1]), parts[-1]

# =====================================
# 🔁 PROCESS MULTIPLE KVIKU FILES
# =====================================
all_outputs = []

for file in kviku_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read KVIKU data with better error handling
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

    # Enhanced mapping with safer date conversions
    output_df['Loan_id'] = 'KV-' + df['Loan N'].astype(str)
    output_df['Debtor_id'] = output_df['Loan_id']
    output_df['Account_number'] = output_df['Loan_id']
    output_df['Debtors_reference_number'] = df['Lifetime ID']
    output_df['Client_name'] = 'Kviku'
    output_df['Product_name'] = df.get('Loan Type', None)
    output_df['Date_of_contract'] = pd.to_datetime(df['Agreement date'].astype(str).str.replace('.', '/'), dayfirst=True, errors='coerce')
    output_df['Loan_amount'] = df['Principal amount']
    output_df['Debtor_name'] = df['Full name']
    output_df['Debtor_birthdate'] = pd.to_datetime(df['DoB'].astype(str).str.replace('.', '/'), dayfirst=True, errors='coerce')
    output_df['email'] = df.get('E-mail', None)
    output_df['Endorsement_date'] = pd.to_datetime(df['Transfer case date'].astype(str).str.replace('.', '/'), dayfirst=True, errors='coerce')
    output_df['DPD'] = df['DPD']
    output_df['Current_DPD'] = output_df['DPD']
    output_df['Due_date'] = output_df['Endorsement_date'] - pd.to_timedelta(output_df['DPD'], unit='D')
    output_df['Last_payment_date'] = pd.to_datetime(df['Last payment date'].astype(str).str.replace('.', '/'), dayfirst=True, errors='coerce').dt.strftime('%d-%b-%Y')
    output_df['Last_payment_amount'] = df.get('Last payment amount', None)
    output_df['Principal_debt'] = df.get('Overdue principal amount', None)
    output_df['Outstanding_balance'] = df.get('Amount to graph', None)
    
    # Enhanced phone formatting
    output_df['Mobile_phone'] = format_phone(df['Mobile N'])
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    output_df['Emergency_contact'] = None
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None

    output_df['Pull_out_date'] = output_df.apply(pullkvi, axis=1)

    # Name splitting
    split_names = df['Full name'].apply(split_name)
    output_df['first_name'] = [x[0] for x in split_names]
    output_df['last_name'] = [x[1] for x in split_names]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_KVIKU_{date_str}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)

    print(f"✅ File successfully saved as: {output_path}")
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
