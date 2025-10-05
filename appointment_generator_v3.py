import pandas as pd
import random
from datetime import datetime, timedelta

# --- V3 Configuration ---
NUM_PATIENTS = 100
SCHEDULING_WINDOW_DAYS = 28
OUTPUT_FILE = 'generated_appointments_v3.csv'

SCHEDULER_IDS = ['scheduler_A_diligent', 'scheduler_B_hasty', 'scheduler_C_forgetful']

# Define the steps and rules for each care plan
CARE_PLANS = {
    'chemo_cycle': {
        'steps': ['Lab', 'Chemo'],
        'rule': lambda dates: (dates['Chemo'] - dates['Lab']).days in range(1, 4)
    },
    'imaging_followup': {
        'steps': ['Mammogram', 'Oncology Visit'],
        'rule': lambda dates: dates['Oncology Visit'] > dates['Mammogram']
    },
    'radiation_prep': {
        'steps': ['CT Simulation', 'Radiation Therapy'],
        'rule': lambda dates: dates['Radiation Therapy'] > dates['CT Simulation']
    },
    'full_workup': {
        'steps': ['CT Chest/Abdomen/Pelvis', 'Bone Scan', 'Oncology Visit'],
        'rule': lambda dates: dates['Oncology Visit'] > dates['CT Chest/Abdomen/Pelvis'] and dates['Oncology Visit'] > dates['Bone Scan']
    }
}

def find_next_available_day(existing_dates, start_date):
    """Finds the next available business day."""
    date_to_check = start_date
    while True:
        if date_to_check.weekday() < 5 and date_to_check.date() not in existing_dates:
            return date_to_check
        date_to_check += timedelta(days=1)

def schedule_plan(scheduler_id, plan_steps, start_date):
    """
    The main scheduling logic that routes to different scheduler behaviors.
    Returns a list of tuples: (datetime_object, appointment_type_string)
    """
    appointments = []
    
    if scheduler_id == 'scheduler_A_diligent':
        # Schedules correctly and tries to consolidate
        current_date = start_date
        for step in plan_steps:
            appt_date = find_next_available_day([d.date() for d, t in appointments], current_date)
            appointments.append((appt_date, step))
            # For the next appointment, try to schedule on the same day
            current_date = appt_date 
        return appointments

    elif scheduler_id == 'scheduler_B_hasty':
        # Schedules correctly but on separate days (inefficient)
        current_date = start_date
        for step in plan_steps:
            appt_date = find_next_available_day([d.date() for d, t in appointments], current_date)
            appointments.append((appt_date, step))
            # For the next appointment, always jump to the next day
            current_date = appt_date + timedelta(days=1)
        return appointments

    else: # scheduler_C_forgetful
        # 50% chance to follow rules, 50% chance to ignore them and just schedule sequentially
        if random.choice([True, False]):
             # Follows the rules (but hastily, like Scheduler B)
            return schedule_plan('scheduler_B_hasty', plan_steps, start_date)
        else:
            # Breaks the rules by reversing the order of the plan
            print(f"   -> Forgetful scheduler is making an error for plan: {plan_steps}")
            return schedule_plan('scheduler_B_hasty', list(reversed(plan_steps)), start_date)

if __name__ == "__main__":
    print("--- Starting V3 Detailed Appointment Generation ---")
    
    all_appointments_list = []
    appt_id_counter = 1
    today = datetime.now()

    for i in range(NUM_PATIENTS):
        patient_mrn = random.randint(1000000, 9999999)
        scheduler_id = random.choice(SCHEDULER_IDS)
        plan_name = random.choice(list(CARE_PLANS.keys()))
        plan_steps = CARE_PLANS[plan_name]['steps']
        
        start_date = today + timedelta(days=random.randint(1, 7))
        
        # Generate the schedule based on the scheduler's personality
        scheduled_appts = schedule_plan(scheduler_id, plan_steps, start_date)
        
        # Format the output with all the required IDs and info
        for appt_datetime, appt_type in scheduled_appts:
            all_appointments_list.append({
                'APPT_ID': appt_id_counter,
                'PATIENT_MRN': patient_mrn,
                'APPT_TYPE': appt_type,
                'APPT_DTTM': appt_datetime,
                'SCHEDULER_ID': scheduler_id
            })
            appt_id_counter += 1

    # Convert to DataFrame
    df = pd.DataFrame(all_appointments_list)
    df = df.sort_values(by=['PATIENT_MRN', 'APPT_DTTM']).reset_index(drop=True)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Successfully generated {len(df)} appointments for {NUM_PATIENTS} patients.")
    print(f"Output saved to '{OUTPUT_FILE}'")
    print("\n--- Data Preview (Now with MRN, Scheduler ID, and APPT ID) ---")
    print(df.head(10))