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
base_dir = r"C:\Users\Windows 11Pro\OneDrive\DA_PROCESS"
month_dir = os.path.join(base_dir, month_full)
endo_base = os.path.join(month_dir, "ENDO_FILE_MAYA")  

endo_folder = f"ENDO_{year}{month_abbr}{day}"
source_dir = os.path.join(endo_base, endo_folder)

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
    print(f"⚠️ Created {endo_folder}. Please place TALA files inside, then rerun the script.")
    exit()

# =====================================
# 🔍 FIND TALA FILES
# =====================================
dpd_files = {}
for file in os.listdir(source_dir):
    if file.startswith("PH.") and "htss_dpd" in file and (file.endswith(".xlsx") or file.endswith(".csv")):
        for dpd in ['36', '52', '112', '172', '232']:
            if f"DPD{dpd}" in file.upper():
                dpd_files[dpd] = os.path.join(source_dir, file)

if not dpd_files:
    print("⚠️ No TALA files found inside ENDO folder.")
    print("Expected filenames like: PH.2025-10-14.xxx.DPD36.htss_dpd_36.full_listing")
    exit()

print(f"✅ Found TALA DPD files: {', '.join(dpd_files.keys())}")

# =====================================
# 🧾 READ TEMPLATE
# =====================================
if not os.path.exists(template_path):
    print(f"⚠️ Template not found at:\n   {template_path}")
    exit()

template_df = pd.read_excel(template_path)
template_cols = template_df.columns.tolist()

# =====================================
# 🔁 PROCESS EACH DPD FILE
# =====================================
def process_tala(df, template):
    output = template.copy()
    output['Debtor_id'] = 'TA-' + df['PERSON_ID'].astype(str)
    output['Account_number'] = 'TA-' + df['LOAN_APPLICATION_ID'].astype(str)
    output['Loan_id'] = 'TA-' + df['LOAN_APPLICATION_ID'].astype(str)
    output['Client_name'] = 'Tala'
    output['Product_name'] = 'cash online loan'
    output['Debtor_name'] = df['NAME']
    output['Due_date'] = df['DUE_DATE']
    output['DPD'] = df['DAYS_PAST_DUE']
    output['Current_DPD'] = df['DAYS_PAST_DUE']
    output['Outstanding_balance'] = df['STILL_OWED']
    output['Mobile_phone'] = "'" + df['PHONE'].astype(str).str.replace('.0','').str.strip()
    output['Alternative_number_1'] = "'" + df['ALTERNATE_PHONE'].astype(str).str.replace('.0','').str.strip()
    output['Alternative_number_1'] = output['Alternative_number_1'].str.replace("'nan","")

    output['Endorsement_date'] = pd.to_datetime(df['HANDOVER_DATE'], errors='coerce')

    # Split NAME into first_name and last_name
    def split_name(name):
        parts = str(name).strip().split()
        if len(parts) == 0:
            return '', ''
        elif len(parts) == 1:
            return parts[0], ''
        else:
            return parts[0], parts[-1]

    split_result = df['NAME'].apply(split_name)
    output['first_name'] = [x[0] for x in split_result]
    output['last_name'] = [x[1] for x in split_result]
    return output

# =====================================
# 📦 PROCESS ALL DPD FILES
# =====================================
all_outputs = []

for dpd, path in dpd_files.items():
    print(f"🔹 Processing DPD {dpd} → {os.path.basename(path)}")

    if path.endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        try:
            df = pd.read_csv(path, encoding='utf-8', low_memory=False)
        except:
            df = pd.read_csv(path, encoding='latin1', low_memory=False)

    df.columns = df.columns.str.strip()  # ensure clean headers

    output_df = process_tala(df, pd.DataFrame(columns=template_cols))
    output_df["DPD"] = dpd
    all_outputs.append(output_df)

# =====================================
# 🧩 COMBINE + SAVE
# =====================================
combined = pd.concat(all_outputs, ignore_index=True)

# --- Combined file ---
combined_filename = f"Template_Fintech_TALA_ALL_{date_str}.xlsx"
combined_path = os.path.join(output_dir, combined_filename)
combined.to_excel(combined_path, index=False)
print(f"✅ Combined TALA file saved: {combined_path}")

# --- Individual DPD files ---
for df in all_outputs:
    dpd = df["DPD"].iloc[0]
    if dpd == '36':
        name = f"Template_Fintech_TALA_36_51_{date_str}.xlsx"
    elif dpd == '52':
        name = f"Template_Fintech_TALA_52_111_{date_str}.xlsx"
    elif dpd == '112':
        name = f"Template_Fintech_TALA_112_171_{date_str}.xlsx"
    elif dpd == '172':
        name = f"Template_Fintech_TALA_172_231_{date_str}.xlsx"
    else:
        name = f"Template_Fintech_TALA_232+_{date_str}.xlsx"

    file_path = os.path.join(output_dir, name)
    df.to_excel(file_path, index=False)
    print(f"📄 Saved DPD {dpd} file: {file_path}")

print("\n🏁 All TALA files processed successfully.")

# Add to each script (talacare.py, salmon.py, etc.)
if __name__ == '__main__':
    try:
        # Your existing script code
        print("✅ Script completed successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)
