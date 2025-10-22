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

# --- MAIN PATHS ---
base_dir = r"C:\Users\Windows 11Pro\OneDrive\DA_PROCESS"
month_dir = os.path.join(base_dir, month_full)
endo_base = os.path.join(month_dir, "ENDO_FILE_MAYA")

# 🔹 Dynamic ENDO folder (e.g., ENDO_2025OCT14)
endo_folder = f"ENDO_{year}{month_abbr}{day}"
source_dir = os.path.join(endo_base, endo_folder)

#1125899948173830 account number check pls after upload



# 🔹 Template & Output folders
template_path = os.path.join(endo_base, "PDS TEMPLATES", "AUTO_TEMPLATES", "Template_Fintech.xlsx")
output_dir = os.path.join(month_dir, "OUTPUT_FOLDER\PDS OUTPUT", month_day)
os.makedirs(output_dir, exist_ok=True)

print(f"Date: {today.strftime('%B %d, %Y')}")
print(f"Expected ENDO folder: {source_dir}")

# =====================================
# 🧩 CHECK OR CREATE ENDO FOLDER
# =====================================
if not os.path.exists(source_dir):
    os.makedirs(source_dir, exist_ok=True)
    print(f"Warning: No ENDO folder found — created {endo_folder}.")
    print("Please place your TALACARE files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND TALACARE FILES (MULTIPLE FILES SUPPORT)
# =====================================
talacare_files = []
for file in os.listdir(source_dir):
    if "TALACARE" in file.upper() and (file.endswith(".xlsx") or file.endswith(".csv")):
        talacare_files.append(os.path.join(source_dir, file))
    elif "lps_loans_in_recoveries" in file.lower() and (file.endswith(".xlsx") or file.endswith(".csv")):
        talacare_files.append(os.path.join(source_dir, file))

if not talacare_files:
    print("⚠️ No TALACARE files found yet inside ENDO folder.")
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
# 🔁 PROCESS MULTIPLE TALACARE FILES
# =====================================
all_outputs = []

for file in talacare_files:
    print(f"🔹 Processing: {os.path.basename(file)}")
    
    # Read TALACARE data with enhanced error handling
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
    output_df['Loan_id'] = df.get('Loan ID', None)
    output_df['Debtor_id'] = df.get('Loan ID', None)
    output_df['Account_number'] = df.get('ACCOUNTNUMBER', None)
    output_df['Debtors_reference_number'] = df.get('Loan Number', None)
    output_df['Client_name'] = 'TALACARE'
    output_df['Product_name'] = df.get('Product Type', None)
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df.get('Selected Date', None), errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df.get('Total_Amount', None)
    output_df['loan_term_days'] = None
    output_df['Debtor_name'] = df.get('Account Name', None)
    output_df['Gender'] = None
    output_df['Debtor_birthdate'] = pd.to_datetime(df.get('DOB', None), errors='coerce')
    output_df['Address'] = df.get('City Name', None)
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = df.get('Employment', None)
    output_df['Salary'] = None
    output_df['Position'] = None
    output_df['email'] = None
    output_df['Due_date'] = pd.to_datetime(df.get('DUE_DATE', None), errors='coerce')
    output_df['DPD'] = df.get('Days Late', None)
    output_df['Current_DPD'] = df.get('Days Late', None)
    output_df['Last_payment_date'] = None
    output_df['Last_payment_amount'] = None
    output_df['Principal_debt'] = df.get('Total_Amount', None)
    output_df['Outstanding_balance'] = df.get('Total_Amount', None)
    output_df['Amount_with_discount'] = None
    output_df['Minimum_payment_amount'] = None

    # Enhanced phone formatting
    output_df['Mobile_phone'] = format_phone(df.get('Phone Number', pd.Series('', index=df.index)))
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    output_df['Emergency_contact'] = format_phone(df.get('Alternate Phone', pd.Series('', index=df.index)))
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None

    output_df['Endorsement_date'] = datetime.today()
    output_df['Pull_out_date'] = datetime.today() + timedelta(days=30)
    output_df['Segment'] = None

    # Name splitting
    split_names = df.get('Account Name', pd.Series('', index=df.index)).apply(split_name)
    output_df['first_name'] = [x[0] for x in split_names]
    output_df['last_name'] = [x[1] for x in split_names]

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE OUTPUT
# =====================================
if all_outputs:
    combined = pd.concat(all_outputs, ignore_index=True)
    output_filename = f"Template_Fintech_TALACARE_{date.today().strftime('%d%m%Y')}.xlsx"
    output_path = os.path.join(output_dir, output_filename)
    combined.to_excel(output_path, index=False)
    print(f"✅ Combined TALACARE file saved: {output_path}")
else:
    print("❌ No files were processed successfully.")

# Add to each script (talacare.py, salmon.py, etc.)
if __name__ == '__main__':
    try:
        # Your existing script code
        print("Script completed successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
