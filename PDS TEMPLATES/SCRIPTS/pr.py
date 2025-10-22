import os
import pandas as pd
from datetime import datetime
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
base_dir = r"C:\Users\Windows 11Pro_HTSS\OneDrive\DA_PROCESS"
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
    print("📥 Please place your PR files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND PR FILES (MULTIPLE FILES SUPPORT)
# =====================================
pr_files = []
for file in os.listdir(source_dir):
    if file.startswith("PR_HTSS") and "(Assign)" in file and (file.endswith(".xlsx") or file.endswith(".csv")):
        pr_files.append(os.path.join(source_dir, file))

if not pr_files:
    print("⚠️ No PR files found yet inside ENDO folder.")
    print("📥 Please place your PR files (e.g., PR_HTSS_2025_10_14(Assign).xlsx) inside:")
    print(f"   {source_dir}")
    exit()

print(f"✅ Found PR files: {pr_files}")

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

def split_name(name):
    if pd.isna(name) or str(name).strip() == '':
        return '', ''
    parts = str(name).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    else:
        return ' '.join(parts[:-1]), parts[-1]

# =====================================
# 🔁 PROCESS MULTIPLE PR FILES
# =====================================
all_outputs = []

for file in pr_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read PR data with enhanced error handling
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

    # Enhanced mapping with safer field access
    output_df['Loan_id'] = df['AgreementNumber']
    output_df['Debtor_id'] = df['AgreementNumber']
    output_df['Account_number'] = df['AgreementNumber']
    output_df['Debtors_reference_number'] = df.get('LifetimeID', None)
    output_df['Client_name'] = 'Peso Redee'
    output_df['Product_name'] = df.get('Product_type', None)
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df.get('DisbursementDate', None), errors='coerce')
    output_df['Loan_amount'] = df.get('InitialAmount', None)
    output_df['Debtor_name'] = df.get('CustomerName', None)
    output_df['Debtor_birthdate'] = pd.to_datetime(df.get('BirthDate', None), errors='coerce')
    output_df['Address'] = df.get('Address', None)
    output_df['email'] = df.get('email', None)
    output_df['Due_date'] = pd.to_datetime(df.get('InitialDueDate', None), errors='coerce')
    output_df['DPD'] = df.get('DPD', None)
    output_df['Current_DPD'] = df.get('DPD', None)
    output_df['Last_payment_date'] = pd.to_datetime(df.get('last_paid_date', None), errors='coerce').dt.strftime('%d-%b-%Y')
    output_df['Last_payment_amount'] = df.get('last_paid_sum', None)
    output_df['Principal_debt'] = df.get('overdue_principal', None)
    output_df['Outstanding_balance'] = df.get('OS', None)
    output_df['Minimum_payment_amount'] = df.get('Min_amount_to_pay', None)

    # Enhanced phone cleaning
    output_df['Mobile_phone'] = format_phone(df.get('MobilePhone', pd.Series('', index=df.index)))
    output_df['Home_phone'] = format_phone(df.get('HomePhone', pd.Series('', index=df.index)))
    output_df['Office_phone'] = format_phone(df.get('Phone', pd.Series('', index=df.index)))
    output_df['Emergency_contact'] = format_phone(df.get('ContactPhone', pd.Series('', index=df.index)))
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None

    output_df['Endorsement_date'] = pd.to_datetime(df.get('start_dt', None), errors='coerce')
    output_df['Pull_out_date'] = pd.to_datetime(df.get('end_dt', None), errors='coerce')
    output_df['Segment'] = df.get('DPD_bucket', None)

    # Name splitting
    split_names = df.get('CustomerName', pd.Series('', index=df.index)).apply(split_name)
    output_df['first_name'] = [x[0] for x in split_names]
    output_df['last_name'] = [x[1] for x in split_names]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_PR_{date_str}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)
    print(f"✅ File successfully saved as: {output_path}")
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
