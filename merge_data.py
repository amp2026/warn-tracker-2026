import pandas as pd
import glob
import os

# This dictionary solves the "Exhaustive" problem by 
# mapping inconsistent state column names to one standard.
COLUMN_MAPPING = {
    # Company Name variations
    'company': 'company_name',
    'employer': 'company_name',
    'organization_name': 'company_name',
    'entity': 'company_name',
    'employer_name': 'company_name',
    
    # Date variations
    'notice_date': 'date_filed',
    'filed_date': 'date_filed',
    'date_received': 'date_filed',
    'notification_date': 'date_filed',
    
    # Impacted Workers variations
    'number_of_workers': 'workers_affected',
    'affected_workers': 'workers_affected',
    'employees_affected': 'workers_affected',
    'layoff_count': 'workers_affected',
    'planned_count': 'workers_affected',
    'worker_count': 'workers_affected'
}

def clean_and_merge():
    # Folder where the 'warn-scraper' saves individual state CSVs
    input_path = './data'
    output_file = 'national_warn_master.csv'
    
    all_files = glob.glob(os.path.join(input_path, "*.csv"))
    
    if not all_files:
        print("No CSV files found in ./data. Run the scraper first!")
        return

    standardized_list = []
    
    for filename in all_files:
        try:
            # Read the state file
            df = pd.read_csv(filename)
            
            # 1. Standardize column names to lowercase and remove spaces
            df.columns = [str(col).lower().strip().replace(' ', '_') for col in df.columns]
            
            # 2. Rename columns based on our mapping dictionary
            df = df.rename(columns=COLUMN_MAPPING)
            
            # 3. Inject the State code (from the filename, e.g., 'ca.csv' -> 'CA')
            state_code = os.path.basename(filename).split('.')[0].upper()
            df['state'] = state_code
            
            # 4. Filter for only the columns we want for the Master List
            # We add 'city' and 'county' in case the state provides them
            core_columns = ['state', 'company_name', 'date_filed', 'workers_affected', 'city', 'county']
            
            # Only keep columns that actually exist in this specific state's file
            available_cols = [c for c in core_columns if c in df.columns]
            df_subset = df[available_cols].copy()
            
            # 5. Data Cleaning: Ensure 'workers_affected' is a number
            if 'workers_affected' in df_subset.columns:
                df_subset['workers_affected'] = pd.to_numeric(
                    df_subset['workers_affected'], errors='coerce'
                ).fillna(0).astype(int)
            
            standardized_list.append(df_subset)
            print(f"Successfully processed: {state_code}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    if standardized_list:
        # Combine all states into one big DataFrame
        master_df = pd.concat(standardized_list, axis=0, ignore_index=True)
        
        # Sort by date (most recent first)
        if 'date_filed' in master_df.columns:
            master_df['date_filed'] = pd.to_datetime(master_df['date_filed'], errors='coerce')
            master_df = master_df.sort_values(by='date_filed', ascending=False)
        
        # Save the exhaustive master file
        master_df.to_csv(output_file, index=False)
        print(f"\n✅ Success! Created {output_file} with {len(master_df)} total records.")
    else:
        print("❌ No data was standardized. Check your column mapping.")

if __name__ == "__main__":
    clean_and_merge()
