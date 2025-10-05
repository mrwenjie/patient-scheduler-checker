import pandas as pd
import random
from datetime import datetime, timedelta, time

# --- V5 Configuration ---
NUM_PATIENTS = 100
OUTPUT_FILE = 'generated_appointments_v5.csv'

SCHEDULER_IDS = ['scheduler_A_diligent', 'scheduler_B_hasty', 'scheduler_C_forgetful']
BUSINESS_HOURS_TIMES = [time(h, m) for h in range(8, 17) for m in (0, 15, 30, 45)]

# V5: Define the small "building blocks" of our care plans
CARE_PLANS = {
    'initial_visit': {'steps': ['Oncology Visit']},
    'chemo_cycle': {'steps': ['Lab', 'Chemo'], 'min_gap_days': 0, 'max_gap_days': 2},
    'imaging_followup': {'steps': ['Mammogram', 'Oncology Visit'], 'min_gap_days': 2, 'max_gap_days': 7},
    'radiation_prep': {'steps': ['CT Simulation', 'Radiation Therapy'], 'min_gap_days': 1, 'max_gap_days': 5}
}

# V5: Define the longitudinal "Master Plans" as a sequence of the building blocks
MASTER_PLANS = {
    'standard_chemo': [
        ('initial_visit', 0), 
        ('chemo_cycle', 2), # Start 2 weeks after initial visit
        ('chemo_cycle', 3), # 3 weeks after previous cycle
        ('chemo_cycle', 3), # 3 weeks after previous cycle
        ('chemo_cycle', 3), # 3 weeks after previous cycle
        ('imaging_followup', 6) # 6 weeks after last chemo
    ],
    'radiation_regimen': [
        ('initial_visit', 0),
        ('radiation_prep', 2), # Start 2 weeks after initial visit
        ('initial_visit', 3), # Mid-radiation checkup
        ('imaging_followup', 8) # 8 weeks after radiation
    ],
    'active_surveillance': [
        ('initial_visit', 0),
        ('imaging_followup', 24), # 6 months (24 weeks) later
        ('imaging_followup', 24)  # another 6 months later
    ]
}

def find_next_available_day(start_date, existing_dates):
    """Finds the next available business day."""
    date_to_check = start_date
    while True:
        if date_to_check.weekday() < 5 and date_to_check.date() not in existing_dates:
            return date_to_check
        date_to_check += timedelta(days=1)

def schedule_phase(scheduler_id, plan_details, start_date, existing_dates):
    """Schedules a single phase (e.g., one chemo cycle) of a master plan."""
    appointments = [] # A list of (datetime, type) tuples
    
    # --- The Diligent Scheduler ---
    if scheduler_id == 'scheduler_A_diligent':
        current_date = start_date
        for i, step in enumerate(plan_details['steps']):
            if i > 0:
                min_gap = plan_details.get('min_gap_days', 1)
                current_date = appointments[-1][0] + timedelta(days=min_gap)
            
            appt_date = find_next_available_day(current_date, existing_dates)
            appt_datetime = appt_date.replace(hour=random.choice(BUSINESS_HOURS_TIMES).hour, minute=random.choice(BUSINESS_HOURS_TIMES).minute)
            appointments.append((appt_datetime, step))
            existing_dates.append(appt_datetime.date())

    # --- Hasty or Forgetful Scheduler ---
    else:
        current_date = start_date
        for step in plan_details['steps']:
            appt_date = find_next_available_day(current_date, existing_dates)
            appt_datetime = appt_date.replace(hour=random.choice(BUSINESS_HOURS_TIMES).hour, minute=random.choice(BUSINESS_HOURS_TIMES).minute)
            appointments.append((appt_datetime, step))
            existing_dates.append(appt_datetime.date())
            current_date = appt_date + timedelta(days=random.randint(2, 5)) # Inefficiently skips a few days

        if scheduler_id == 'scheduler_C_forgetful' and random.random() < 0.4: # 40% chance of error
            print(f"   -> Forgetful scheduler is making an error for plan: {plan_details['steps']}")
            if len(appointments) > 1 and plan_details.get('min_gap_days', 1) > 0:
                # Error: Put appointments that need a gap on the same day
                base_date = appointments[0][0]
                for i in range(1, len(appointments)):
                    appointments[i] = (base_date.replace(hour=random.choice(BUSINESS_HOURS_TIMES).hour, minute=random.choice(BUSINESS_HOURS_TIMES).minute), appointments[i][1])
            elif len(appointments) > 1:
                # Error: Reverse the order
                appointments.reverse()
                
    return appointments, existing_dates

if __name__ == "__main__":
    print("--- Starting V5 Longitudinal Patient Journey Simulation ---")
    
    all_appointments_list = []
    generated_appt_ids = set()
    today = datetime.now()

    for i in range(NUM_PATIENTS):
        patient_mrn = random.randint(1000000, 9999999)
        scheduler_id = random.choice(SCHEDULER_IDS)
        master_plan_name = random.choice(list(MASTER_PLANS.keys()))
        master_plan = MASTER_PLANS[master_plan_name]
        
        print(f"Processing MRN {patient_mrn}: Plan='{master_plan_name}', Scheduler='{scheduler_id}'")

        time_cursor = today + timedelta(days=random.randint(1, 14))
        patient_scheduled_dates = []

        for phase_name, weeks_after in master_plan:
            time_cursor += timedelta(weeks=weeks_after)
            plan_details = CARE_PLANS[phase_name]
            
            scheduled_phase_appts, patient_scheduled_dates = schedule_phase(
                scheduler_id, plan_details, time_cursor, patient_scheduled_dates
            )
            
            # Format and add to the master list
            for appt_datetime, appt_type in scheduled_phase_appts:
                while True:
                    appt_id = f"APT-{random.randint(10000000, 99999999)}"
                    if appt_id not in generated_appt_ids:
                        generated_appt_ids.add(appt_id)
                        break

                all_appointments_list.append({
                    'APPT_ID': appt_id,
                    'PATIENT_MRN': patient_mrn,
                    'APPT_TYPE': appt_type,
                    'APPT_DTTM': appt_datetime,
                    'SCHEDULER_ID': scheduler_id
                })
            
            # Update the time cursor to be after the last scheduled appointment in the phase
            if scheduled_phase_appts:
                time_cursor = scheduled_phase_appts[-1][0]


    df = pd.DataFrame(all_appointments_list)
    df = df.sort_values(by=['PATIENT_MRN', 'APPT_DTTM']).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Successfully generated {len(df)} longitudinal appointments for {NUM_PATIENTS} patients.")
    print(f"Output saved to '{OUTPUT_FILE}'")
    print("\n--- V5 Data Preview ---")
    # Show appointments for one patient to demonstrate the journey
    if len(df) > 0:
        first_mrn = df['PATIENT_MRN'].iloc[0]
        print(df[df['PATIENT_MRN'] == first_mrn])