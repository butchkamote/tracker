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
month_abbr = today.strftime('%b').upper()       # OCT
month_full = today.strftime('%B').upper()       # OCTOBER
day = today.strftime('%d')
date_str = today.strftime('%Y_%m_%d')
month_day = f"{month_abbr.lower()}_{day}"

# --- MAIN PATHS ---
base_dir = r"C:\Users\Windows 11Pro\OneDrive\DA_PROCESS"
month_dir = os.path.join(base_dir, month_full)
endo_base = os.path.join(month_dir, "ENDO_FILE_MAYA")  

# 🔹 Dynamic ENDO folder (ENDO_YYYYMMMDD)
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
    print("📥 Please place your OLP files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND TALACARE FILES
# =====================================
talacare_files = []
for file in os.listdir(source_dir):
    if "TALACARE" in file.upper() and (file.endswith(".xlsx") or file.endswith(".csv")):
        talacare_files.append(os.path.join(source_dir, file))

if not talacare_files:
    print("⚠️ No OLP files found yet inside ENDO folder.")
    exit()

print(f"✅ Found TALACARE files: {talacare_files}")

# =====================================
# 🧾 READ TEMPLATE
# =====================================
if not os.path.exists(template_path):
    print(f"⚠️ Fintech template not found at:\n   {template_path}")
    exit()

template_df = pd.read_excel(template_path)
template_cols = template_df.columns.tolist()

# =====================================
# 🧹 PHONE FORMATTING FUNCTION
# =====================================
def format_phone(series):
    # Replace leading country code 63 with 0, remove non-digits, ensure max 11 digits
    return (
        '0' + series.astype(str).str.replace(r'\.0$', '', regex=True)
        .str.replace(r'\D', '', regex=True).str[-10:]
    )

# =====================================
# 🧩 NAME SPLIT FUNCTION
# =====================================
def split_name(name):
    if pd.isna(name) or str(name).strip() == '':
        return '', ''
    parts = str(name).strip().split()
    if len(parts) == 1:
        return parts[0], ''
    else:
        return ' '.join(parts[:-1]), parts[-1]

# =====================================
# 🔁 MAP TALACARE → FINTECH TEMPLATE
# =====================================
all_outputs = []

for file in talacare_files:
    # Read raw file
    if file.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file, encoding='utf-8', low_memory=False)

    output_df = pd.DataFrame(columns=template_cols)

    # Mapping
    output_df['Loan_id'] = df['Loan ID']
    output_df['Debtor_id'] = df['Loan ID']  # same as Loan_id
    output_df['Account_number'] = df['ACCOUNTNUMBER']
    output_df['Debtors_reference_number'] = df['Loan Number']
    output_df['Client_name'] = 'TALACARE'
    output_df['Product_name'] = df.get('Product Type', None)
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df['Selected Date'], errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df['Total_Amount']
    output_df['loan_term_days'] = None
    output_df['Debtor_name'] = df['Account Name']
    output_df['Gender'] = None
    output_df['Debtor_birthdate'] = pd.to_datetime(df.get('DOB', None), errors='coerce')
    output_df['Address'] = df.get('City Name', None)
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = df.get('Employment', None)
    output_df['Salary'] = None
    output_df['Position'] = None
    output_df['email'] = None
    output_df['Due_date'] = pd.to_datetime(df['DUE_DATE'], errors='coerce')
    output_df['DPD'] = df['Days Late']
    output_df['Current_DPD'] = df['Days Late']
    output_df['Last_payment_date'] = None
    output_df['Last_payment_amount'] = None
    output_df['Principal_debt'] = df['Total_Amount']  # same as loan_amount
    output_df['Outstanding_balance'] = df['Total_Amount']  # same as loan_amount
    output_df['Amount_with_discount'] = None
    output_df['Minimum_payment_amount'] = None
    output_df['Mobile_phone'] = format_phone(df['Phone Number'])
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    output_df['Emergency_contact'] = format_phone(df.get('Alternate Phone', pd.Series('', index=df.index)))
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None
    output_df['Endorsement_date'] = datetime.today()
    output_df['Pull_out_date'] = datetime.today() + timedelta(days=30)
    output_df['Segment'] = None

    # first_name / last_name
    first_last = df['Account Name'].apply(split_name)
    output_df['first_name'] = [x[0] for x in first_last]
    output_df['last_name'] = [x[1] for x in first_last]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE
# =====================================
combined = pd.concat(all_outputs, ignore_index=True)
output_file = os.path.join(output_dir, f"Template_Fintech_TALACARE_{date.today().strftime('%d%m%Y')}.xlsx")
combined.to_excel(output_file, index=False)
print(f"✅ Combined TALACARE file saved: {output_file}")

# Add to each script (talacare.py, salmon.py, etc.)
if __name__ == '__main__':
    try:
        # Your existing script code
        print("✅ Script completed successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)
