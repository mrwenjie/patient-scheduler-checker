import pandas as pd
from datetime import datetime, timedelta

# --- Configuration ---
INPUT_FILE = 'generated_appointments_v5.csv'
LOOKAHEAD_DAYS = 60 * 2 # Let's look further ahead to catch more of the generated journey, e.g., 4 months

def find_related_appointment(df, appt_type, base_time, time_window_days):
    """
    Looks for a specific type of appointment within a time window around a base time.
    Returns the appointment's datetime if found, otherwise None.
    """
    start_window = base_time - timedelta(days=time_window_days)
    end_window = base_time + timedelta(days=time_window_days)
    
    related_appts = df[
        (df['APPT_TYPE'] == appt_type) &
        (df['APPT_DTTM'] >= start_window) &
        (df['APPT_DTTM'] <= end_window)
    ]
    
    if not related_appts.empty:
        return related_appts['APPT_DTTM'].iloc[0]
    return None

def check_patient_schedule(patient_appts):
    """
    Analyzes a single patient's full schedule for any rule violations.
    This is the new, more robust core logic.
    """
    flags = []
    
    # Sort appointments chronologically
    patient_appts = patient_appts.sort_values('APPT_DTTM')
    
    # Iterate through each appointment to check for rule violations
    for index, current_appt in patient_appts.iterrows():
        appt_type = current_appt['APPT_TYPE']
        appt_time = current_appt['APPT_DTTM']

        # --- Rule Check for "Chemo" ---
        if appt_type == 'Chemo':
            lab_time = find_related_appointment(patient_appts, 'Lab', appt_time, time_window_days=7)
            if lab_time is None:
                flags.append(f"Critical Error: A Chemo on {appt_time.date()} has no Lab test scheduled within the prior 7 days.")
            else:
                if lab_time > appt_time:
                    flags.append(f"Order Error: Lab on {lab_time.date()} is AFTER Chemo on {appt_time.date()}.")
                elif (appt_time.date() - lab_time.date()).days < 1:
                    flags.append(f"Timing Error: Lab on {lab_time.date()} is on the same day as Chemo on {appt_time.date()}. Must be at least 1 day prior.")

        # --- Rule Check for "Oncology Visit" after an imaging scan ---
        if appt_type == 'Oncology Visit':
            mammo_time = find_related_appointment(patient_appts, 'Mammogram', appt_time, time_window_days=14)
            if mammo_time and mammo_time > appt_time:
                flags.append(f"Order Error: Oncology Visit on {appt_time.date()} is BEFORE its related Mammogram on {mammo_time.date()}.")
            elif mammo_time and (appt_time.date() - mammo_time.date()).days < 2:
                 flags.append(f"Timing Error: Visit on {appt_time.date()} is too soon after Mammogram on {mammo_time.date()} (requires 2-day gap for results).")

        # --- Rule Check for "Radiation Therapy" ---
        if appt_type == 'Radiation Therapy':
             sim_time = find_related_appointment(patient_appts, 'CT Simulation', appt_time, time_window_days=14)
             if sim_time and sim_time > appt_time:
                 flags.append(f"Order Error: Radiation Therapy on {appt_time.date()} is BEFORE its planning CT Simulation on {sim_time.date()}.")

    return list(set(flags)) # Return unique flags

def format_and_send_reports(flagged_patients_df):
    """Simulates sending an email report to each scheduler."""
    print("\n" + "="*50)
    print("--- GENERATING SCHEDULER ERROR REPORTS ---")
    print("="*50 + "\n")
    
    if flagged_patients_df.empty:
        print("✅ No scheduling errors were found in the upcoming appointments.")
        return
        
    for scheduler_id, group in flagged_patients_df.groupby('SCHEDULER_ID'):
        print(f"--- Email Report for: {scheduler_id} ---")
        print("Subject: Daily Patient Schedule Review Required\n")
        print("Hello,\nThe automated monitoring system has flagged the following patient schedules for your review:\n")
        
        for mrn, patient_flags in group.groupby('PATIENT_MRN'):
            print(f"  - PATIENT MRN: {mrn}")
            for flag in patient_flags['FLAGS'].iloc[0]:
                print(f"    - Reason: {flag}")
            print("")
            
        print("Thank you,\nClinical Informatics System\n")
        print("--- End of Report ---\n\n")

if __name__ == "__main__":
    try:
        df_all = pd.read_csv(INPUT_FILE, parse_dates=['APPT_DTTM'])
    except FileNotFoundError:
        print(f"Error: The input file '{INPUT_FILE}' was not found. Please run an appointment generator script first.")
        exit()

    print(f"Loaded {len(df_all)} total appointments from '{INPUT_FILE}'.")

    today = datetime.now()
    future_date_limit = today + timedelta(days=LOOKAHEAD_DAYS)
    
    df_filtered = df_all[(df_all['APPT_DTTM'] >= today) & (df_all['APPT_DTTM'] <= future_date_limit)].copy()
    
    print(f"Filtered to {len(df_filtered)} appointments scheduled in the next {LOOKAHEAD_DAYS} days.")

    if df_filtered.empty:
        print("No upcoming appointments found in the specified date range. Exiting.")
        exit()

    all_flags = []
    
    # Iterate through each patient in the filtered data
    for mrn, patient_appts in df_filtered.groupby('PATIENT_MRN'):
        flags_found = check_patient_schedule(patient_appts)
        
        if flags_found:
            scheduler_id = patient_appts['SCHEDULER_ID'].iloc[0]
            all_flags.append({
                'PATIENT_MRN': mrn,
                'SCHEDULER_ID': scheduler_id,
                'FLAGS': flags_found
            })

    flagged_df = pd.DataFrame(all_flags)
    format_and_send_reports(flagged_df)