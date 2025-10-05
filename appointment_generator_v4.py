import pandas as pd
import random
from datetime import datetime, timedelta

# --- V4 Configuration ---
NUM_PATIENTS = 100
SCHEDULING_WINDOW_DAYS = 28
OUTPUT_FILE = 'generated_appointments_v4.csv'

SCHEDULER_IDS = ['scheduler_A_diligent', 'scheduler_B_hasty', 'scheduler_C_forgetful']

# Generate realistic appointment time slots (8:00 AM to 4:30 PM every 15 mins)
BUSINESS_HOURS_TIMES = [f"{h:02d}:{m:02d}" for h in range(8, 17) for m in (0, 15, 30, 45)]

# V4: More powerful Care Plan definitions with rules
CARE_PLANS = {
    'chemo_cycle': {
        'steps': ['Lab', 'Chemo'],
        'min_gap_days': 0, # Can be on the same day
        'max_gap_days': 2
    },
    'imaging_followup': {
        'steps': ['Mammogram', 'Oncology Visit'],
        'min_gap_days': 2, # Need 2 days for results
        'max_gap_days': 7
    },
    'radiation_prep': {
        'steps': ['CT Simulation', 'Radiation Therapy'],
        'min_gap_days': 1, # Can be next day
        'max_gap_days': 5
    }
}

def get_random_datetime(base_date):
    """Combines a date with a random business-hour time slot."""
    time_str = random.choice(BUSINESS_HOURS_TIMES)
    hour, minute = map(int, time_str.split(':'))
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

def schedule_plan(scheduler_id, plan, start_date):
    """Schedules a list of appointments based on scheduler personality and plan rules."""
    appointments = []
    
    # --- The Diligent Scheduler ---
    if scheduler_id == 'scheduler_A_diligent':
        current_date = start_date
        for i, step in enumerate(plan['steps']):
            if i == 0:
                # Schedule the first appointment
                appt_date = current_date
            else:
                # Schedule subsequent appointments based on rules
                previous_appt_date = appointments[-1][0]
                # Start looking for a slot after the minimum gap
                current_date = previous_appt_date + timedelta(days=plan['min_gap_days'])
                appt_date = current_date
            
            # Find a valid weekday
            while appt_date.weekday() >= 5: # 5 is Saturday, 6 is Sunday
                appt_date += timedelta(days=1)
            
            appointments.append((get_random_datetime(appt_date), step))

    # --- The Hasty or Forgetful Scheduler ---
    else:
        # Hasty and Forgetful both start by being inefficient
        current_date = start_date
        for step in plan['steps']:
            # Find the next available weekday
            while current_date.weekday() >= 5:
                current_date += timedelta(days=1)
            appointments.append((get_random_datetime(current_date), step))
            # Always jump to the next day, creating inefficiency
            current_date += timedelta(days=random.randint(1,3))

        # The Forgetful scheduler has a chance to break the rules
        if scheduler_id == 'scheduler_C_forgetful' and random.choice([True, False]):
            print(f"   -> Forgetful scheduler is making an error for plan: {plan['steps']}")
            # Error 1: Reverse the order of appointments
            if random.choice([True, False]):
                appointments.reverse()
            # Error 2: Ignore min_gap and put appointments on the same day
            else:
                base_date = appointments[0][0]
                for i in range(1, len(appointments)):
                    appointments[i] = (get_random_datetime(base_date), appointments[i][1])

    return appointments

if __name__ == "__main__":
    print("--- Starting V4 Realistic Appointment Generation ---")
    
    all_appointments_list = []
    generated_appt_ids = set()
    today = datetime.now()

    for i in range(NUM_PATIENTS):
        patient_mrn = random.randint(1000000, 9999999)
        scheduler_id = random.choice(SCHEDULER_IDS)
        plan_name = random.choice(list(CARE_PLANS.keys()))
        plan = CARE_PLANS[plan_name]
        
        start_date = today + timedelta(days=random.randint(1, SCHEDULING_WINDOW_DAYS - 10))
        
        scheduled_appts = schedule_plan(scheduler_id, plan, start_date)
        
        for appt_datetime, appt_type in scheduled_appts:
            # Generate a unique, longer appointment ID
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

    # Convert, sort, and save
    df = pd.DataFrame(all_appointments_list)
    df = df.sort_values(by=['PATIENT_MRN', 'APPT_DTTM']).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n✅ Successfully generated {len(df)} appointments for {NUM_PATIENTS} patients.")
    print(f"Output saved to '{OUTPUT_FILE}'")
    print("\n--- V4 Data Preview (Realistic IDs, Times, and Logic) ---")
    print(df.head(10))