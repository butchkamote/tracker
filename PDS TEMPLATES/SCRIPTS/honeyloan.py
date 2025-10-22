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
    print("📥 Please place your HONEYLOAN files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND HONEYLOAN FILES (MULTIPLE FILES SUPPORT)
# =====================================
honeyloan_files = []
for file in os.listdir(source_dir):
    if "honeyloan" in file.lower() or "honey_loan" in file.lower() or "honey loan" in file.lower():
        if file.endswith(".xlsx") or file.endswith(".csv"):
            honeyloan_files.append(os.path.join(source_dir, file))

if not honeyloan_files:
    print("⚠️ No HONEYLOAN files found yet inside ENDO folder.")
    print("📥 Please place your HONEYLOAN files inside:")
    print(f"   {source_dir}")
    exit()

print(f"✅ Found HONEYLOAN files: {honeyloan_files}")

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
def format_phone_honeyloan(series):
    # Handle NaN and empty values
    if series is None or pd.isna(series).all():
        return pd.Series('', index=series.index if hasattr(series, 'index') else [])
    
    # Convert to string and clean
    formatted = (
        '0' + series.astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.replace(r'\D', '', regex=True)
        .str[-10:]
    )
    
    return formatted

# =====================================
# 🧩 HELPER FUNCTIONS
# =====================================
def split_debtor_name(debtor_name):
    if pd.isna(debtor_name) or str(debtor_name).strip() == '':
        return '', ''
    
    name_parts = str(debtor_name).strip().split()
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
# 🔁 PROCESS MULTIPLE HONEYLOAN FILES
# =====================================
all_outputs = []

for file in honeyloan_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read HONEYLOAN data with enhanced error handling
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

    # Enhanced mapping with your HoneyLoan mapping logic
    output_df['Loan_id'] = 'HL-' + df.get('loan_id', pd.Series('', index=df.index)).astype(str)
    output_df['Debtor_id'] = 'HL-' + df.get('agreementnumber', pd.Series('', index=df.index)).astype(str)
    output_df['Account_number'] = 'HL-' + df.get('agreementnumber', pd.Series('', index=df.index)).astype(str)
    output_df['Debtors_reference_number'] = df.get('lifetime_id', None)
    output_df['Client_name'] = df.get('client_name', None)
    output_df['Product_name'] = df.get('product', None)
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df.get('disbursementdate', None), errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df.get('initialamount', None)
    output_df['loan_term_days'] = None
    output_df['Debtor_name'] = df.get('debtor_name', None)
    output_df['Gender'] = None
    output_df['Debtor_birthdate'] = pd.to_datetime(df.get('birthdate', None), errors='coerce')
    output_df['Address'] = df.get('permanent_address', None)
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = df.get('employer_name', None)
    output_df['Salary'] = df.get('salary', None)
    output_df['Position'] = None
    output_df['email'] = df.get('e_mail', None)
    output_df['Due_date'] = pd.to_datetime(df.get('initialduedate', None), errors='coerce')
    output_df['DPD'] = df.get('dpd', None)
    output_df['Current_DPD'] = df.get('dpd', None)
    output_df['Last_payment_date'] = None
    output_df['Last_payment_amount'] = None
    output_df['Principal_debt'] = df.get('principal', None)
    output_df['Outstanding_balance'] = df.get('targeted_amount', None)
    output_df['Amount_with_discount'] = None
    output_df['Minimum_payment_amount'] = df.get('mininum_payment', None)

    # Enhanced phone formatting using your logic
    output_df['Mobile_phone'] = format_phone_honeyloan(df.get('mobilephone', pd.Series('', index=df.index)))
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    output_df['Emergency_contact'] = format_phone_honeyloan(df.get('contact_person_mobile_phone', pd.Series('', index=df.index)))
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None

    # Date assignments from your mapping
    output_df['Endorsement_date'] = pd.to_datetime(df.get('date_of_assignment', None), errors='coerce')
    output_df['Pull_out_date'] = pd.to_datetime(df.get('date_of_abortion', None), errors='coerce')
    output_df['Segment'] = None

    # Name splitting using your split_debtor_name function
    name_split = df.get('debtor_name', pd.Series('', index=df.index)).apply(split_debtor_name)
    output_df['first_name'] = [x[0] for x in name_split]
    output_df['last_name'] = [x[1] for x in name_split]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_HONEYLOAN_{date_str}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)
    print(f"✅ Combined HONEYLOAN file saved: {output_path}")
    print("✅ You can now upload this file to the PDS portal.")
else:
    print("❌ No files were processed successfully.")