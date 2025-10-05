import pandas as pd
import random
from datetime import datetime, timedelta

# --- Configuration ---
NUM_PATIENTS = 100
SCHEDULING_WINDOW_DAYS = 60  # Expanded window to 2 months
OUTPUT_FILE = 'generated_appointments_v2.csv'

# --- Helper Functions (same as before) ---
def find_next_available_day(existing_appts, start_date):
    date_to_check = start_date
    existing_dates = [d['APPT_DTTM'].date() for d in existing_appts]
    while True:
        if date_to_check.weekday() < 5 and date_to_check.date() not in existing_dates:
            return date_to_check
        date_to_check += timedelta(days=1)

# --- IMAGING BUNDLE SCHEDULERS (same as before) ---
def schedule_imaging_diligent(existing_appts, start_date):
    new_appts = []
    pet_ct_date = find_next_available_day(existing_appts, start_date)
    new_appts.append({'APPT_DTTM': pet_ct_date, 'APPT_TYPE': 'PET-CT'})
    visit_date = find_next_available_day(existing_appts + new_appts, pet_ct_date)
    new_appts.append({'APPT_DTTM': visit_date, 'APPT_TYPE': 'Doctor Visit'})
    return new_appts

def schedule_imaging_hasty(existing_appts, start_date):
    new_appts = []
    pet_ct_date = find_next_available_day(existing_appts, start_date)
    new_appts.append({'APPT_DTTM': pet_ct_date, 'APPT_TYPE': 'PET-CT'})
    next_day_start = pet_ct_date + timedelta(days=1)
    visit_date = find_next_available_day(existing_appts + new_appts, next_day_start)
    new_appts.append({'APPT_DTTM': visit_date, 'APPT_TYPE': 'Doctor Visit'})
    return new_appts
    
def schedule_imaging_forgetful(existing_appts, start_date):
    new_appts = []
    remembers_rule = random.choice([True, False])
    first_appt_date = find_next_available_day(existing_appts, start_date)
    second_appt_date = find_next_available_day(existing_appts + [{'APPT_DTTM': first_appt_date}], first_appt_date + timedelta(days=1))
    if remembers_rule:
        new_appts.append({'APPT_DTTM': first_appt_date, 'APPT_TYPE': 'PET-CT'})
        new_appts.append({'APPT_DTTM': second_appt_date, 'APPT_TYPE': 'Doctor Visit'})
    else:
        new_appts.append({'APPT_DTTM': first_appt_date, 'APPT_TYPE': 'Doctor Visit'})
        new_appts.append({'APPT_DTTM': second_appt_date, 'APPT_TYPE': 'PET-CT'})
    return new_appts

# --- NEW: CHEMO BUNDLE SCHEDULERS ---
def schedule_chemo_diligent(existing_appts, start_date):
    new_appts = []
    # 1. Schedule Chemo first
    chemo_date = find_next_available_day(existing_appts, start_date)
    new_appts.append({'APPT_DTTM': chemo_date, 'APPT_TYPE': 'Chemo'})
    # 2. Schedule Lab 1 or 2 days before
    lab_date_target = chemo_date - timedelta(days=random.randint(1, 2))
    # Ensure lab date is valid and available
    lab_date = find_next_available_day(existing_appts, lab_date_target)
    new_appts.append({'APPT_DTTM': lab_date, 'APPT_TYPE': 'Lab'})
    return new_appts

def schedule_chemo_hasty(existing_appts, start_date):
    new_appts = []
    # Schedules Lab and Chemo far apart
    lab_date = find_next_available_day(existing_appts, start_date)
    new_appts.append({'APPT_DTTM': lab_date, 'APPT_TYPE': 'Lab'})
    # Schedules chemo at least a week later
    chemo_start_date = lab_date + timedelta(days=7)
    chemo_date = find_next_available_day(existing_appts + new_appts, chemo_start_date)
    new_appts.append({'APPT_DTTM': chemo_date, 'APPT_TYPE': 'Chemo'})
    return new_appts

def schedule_chemo_forgetful(existing_appts, start_date):
    new_appts = []
    # 50% chance of making a timing error (same day)
    makes_timing_error = random.choice([True, False])
    
    if makes_timing_error:
        print(f"   -> Forgetful scheduler made a SAME-DAY chemo error!")
        same_day = find_next_available_day(existing_appts, start_date)
        new_appts.append({'APPT_DTTM': same_day, 'APPT_TYPE': 'Lab'})
        new_appts.append({'APPT_DTTM': same_day, 'APPT_TYPE': 'Chemo'})
    else:
        # Correctly schedules on different days, but might still get the order wrong
        return schedule_chemo_diligent(existing_appts, start_date)
    return new_appts


if __name__ == "__main__":
    print("--- Starting V2 Appointment Generation Simulation ---")
    
    patient_ids = [f"PAT_{i:03d}" for i in range(1, NUM_PATIENTS + 1)]
    all_appointments = []
    today = datetime.now()

    for patient_id in patient_ids:
        # For each patient, randomly choose to schedule an imaging bundle OR a chemo bundle
        bundle_type = random.choice(['imaging', 'chemo'])
        scheduler_type = random.choice(['diligent', 'hasty', 'forgetful'])
        print(f"Processing {patient_id}: Bundle='{bundle_type}', Scheduler='{scheduler_type}'...")
        
        existing_appts_for_patient = [] 
        start_date = today + timedelta(days=random.randint(1, 14))

        if bundle_type == 'imaging':
            if scheduler_type == 'diligent':
                new_appts = schedule_imaging_diligent(existing_appts_for_patient, start_date)
            elif scheduler_type == 'hasty':
                new_appts = schedule_imaging_hasty(existing_appts_for_patient, start_date)
            else: # forgetful
                new_appts = schedule_imaging_forgetful(existing_appts_for_patient, start_date)
        else: # chemo
            if scheduler_type == 'diligent':
                new_appts = schedule_chemo_diligent(existing_appts_for_patient, start_date)
            elif scheduler_type == 'hasty':
                new_appts = schedule_chemo_hasty(existing_appts_for_patient, start_date)
            else: # forgetful
                new_appts = schedule_chemo_forgetful(existing_appts_for_patient, start_date)

        # Add patient ID to the generated appointments and add to master list
        for appt in new_appts:
            appt['PAT_ID'] = patient_id
        all_appointments.extend(new_appts)

    # Convert to DataFrame, sort, and save
    df = pd.DataFrame(all_appointments)
    df = df.sort_values(by=['PAT_ID', 'APPT_DTTM']).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n✅ Successfully generated {len(df)} appointments for {NUM_PATIENTS} patients.")
    print(f"Output saved to '{OUTPUT_FILE}'")
    print("\n--- Data Preview ---")
    print(df.head(10))