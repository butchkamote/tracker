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
    print("📥 Please place your SKYRO files inside this folder, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND SKYRO FILES
# =====================================
skyro_files = []
for file in os.listdir(source_dir):
    if "SKYRO" in file.upper() and (file.endswith(".xlsx") or file.endswith(".csv")):
        skyro_files.append(os.path.join(source_dir, file))

if not skyro_files:
    print("⚠️ No SKYRO files found yet inside ENDO folder.")
    exit()

print(f"✅ Found SKYRO files: {skyro_files}")

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
    return (
        '0' + series.astype(str).str.replace(r'\.0$', '', regex=True)
        .str.replace(r'\D', '', regex=True).str[-10:]
    )

# =====================================
# 🔁 MAP SKYRO → FINTECH TEMPLATE
# =====================================
all_outputs = []

for file in skyro_files:
    # Read raw file
    if file.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file, encoding='utf-8', low_memory=False)

    output_df = pd.DataFrame(columns=template_cols)

    # Mapping based on provided SKYRO function
    output_df['Loan_id'] = df['ACCOUNT_NUMBER'].astype(str)
    output_df['Debtor_id'] = df['PERSON_ID']
    output_df['Account_number'] = df['ACCOUNT_NUMBER']
    output_df['Debtors_reference_number'] = df['STATIC_REFERENCE_NO']
    output_df['Client_name'] = 'Skyro'
    output_df['Product_name'] = df['PRODUCT_NM']
    output_df['Goods_purchased'] = None
    output_df['Date_of_contract'] = pd.to_datetime(df['OPEN_DT'], errors='coerce')
    output_df['Date_contract_end'] = None
    output_df['Loan_amount'] = df['PRINCIPAL_BALANCE_AMT_EOD']
    output_df['loan_term_days'] = None
    output_df['Debtor_name'] = df['FIRST_NM'] + ' ' + df['LAST_NM']
    output_df['Gender'] = None
    output_df['Debtor_birthdate'] = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
    output_df['Address'] = None
    output_df['Maritual_status'] = None
    output_df['Emloyer_name'] = None
    output_df['Salary'] = None
    output_df['Position'] = None
    output_df['email'] = df['EMAIL_ADDRESS']
    
    # Calculate Due date from START_DT and DPD
    output_df['Due_date'] = pd.to_datetime(df['START_DT'], errors='coerce') - pd.to_timedelta(df['DPD'], unit='D')
    
    output_df['DPD'] = df['DPD']
    output_df['Current_DPD'] = df['DPD']
    output_df['Last_payment_date'] = pd.to_datetime(df['LAST_PAYMENT_DATE'], errors='coerce')
    output_df['Last_payment_amount'] = df['LAST_PAYMENT_AMOUNT']
    output_df['Principal_debt'] = df['PRINCIPAL_BALANCE_AMT_EOD']
    output_df['Outstanding_balance'] = df['BALANCE_AMT_EOD']
    output_df['Amount_with_discount'] = None
    output_df['Minimum_payment_amount'] = None
    
    # Phone number formatting
    output_df['Mobile_phone'] = '0' + df['PHONE'].astype(str).str.replace('.0','').str[2:]
    output_df['Home_phone'] = None
    output_df['Office_phone'] = None
    
    # Emergency contact formatting
    emergency_contacts = df['ADDITIONAL_CONTACTS'].str.extract(r'(\d+)')
    output_df['Emergency_contact'] = '0' + emergency_contacts[0].str[2:]
    
    output_df['Alternative_number_1'] = None
    output_df['Alternative_number_2'] = None
    output_df['Alternative_number_3'] = None
    output_df['Endorsement_date'] = pd.to_datetime(df['START_DT'], errors='coerce')
    output_df['Pull_out_date'] = output_df['Endorsement_date'] + timedelta(days=30)
    output_df['Segment'] = None
    
    # Split name into first and last
    output_df['first_name'] = df['FIRST_NM']
    output_df['last_name'] = df['LAST_NM']

    all_outputs.append(output_df)

# =====================================
# 💾 COMBINE & SAVE
# =====================================
combined = pd.concat(all_outputs, ignore_index=True)
output_file = os.path.join(output_dir, f"Template_Fintech_SKYRO_{date.today().strftime('%d%m%Y')}.xlsx")
combined.to_excel(output_file, index=False)
print(f"✅ Combined SKYRO file saved: {output_file}")

# Add to each script (talacare.py, salmon.py, etc.)
if __name__ == '__main__':
    try:
        # Your existing script code
        print("✅ Script completed successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)