#!/usr/bin/env python3
"""
Cron job script to process pending reactor experiments
This script should be run periodically to process experiments in the queue
"""

import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime
from dotenv import load_dotenv

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import db
from EXPERIMENT_MODEL import Laboratory_process

# Load environment variables
load_dotenv()

def process_pending_experiments():
    """Process all pending experiments in the database"""
    print(f"[{datetime.now()}] Starting experiment processing...")
    
    # First, reset any timed-out experiments
    timeout_reset_count = db.reset_timed_out_experiments()
    if timeout_reset_count > 0:
        print(f"Reset {timeout_reset_count} timed-out experiments")
    
    # Get pending experiments
    pending_experiments = db.get_pending_experiments()
    
    if not pending_experiments:
        print("No pending experiments found.")
        return
    
    print(f"Found {len(pending_experiments)} pending experiments")
    
    # Get max tries from environment variable
    max_tries = int(os.getenv('TRIES_TO_FAIL_EXPERIMENT', '3'))
    
    for experiment in pending_experiments:
        try:
            print(f"Processing experiment {experiment['id']}: {experiment['experiment_name']} (tries: {experiment['number_of_tries']})")
            
            # Check if experiment has exceeded max tries
            if experiment['number_of_tries'] >= max_tries:
                error_msg = f"Experiment failed after {experiment['number_of_tries']} attempts"
                db.mark_experiment_failed_permanently(experiment['id'], error_msg)
                print(f"Experiment {experiment['id']} marked as permanently failed (exceeded {max_tries} tries)")
                continue
            
            # Update status to running
            db.update_experiment_status(experiment['id'], 'running')
            
            # Get experiment parameters
            parameters = db.get_reactor_parameters(experiment['id'])
            
            # Read Excel file
            excel_file_path = experiment['excel_file_path']
            if not os.path.exists(excel_file_path):
                raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
            
            # Read Excel file and convert to the format expected by the model
            data = pd.read_excel(excel_file_path)
            
            # Validate required columns
            required_columns = ['t[s]', 'F2[m^3/s]', 'F7[m^3/s]', 'F8[m^3/s]', 'F9[m^3/s]', 
                              'RPS[RPS]', 'T1[K]', 'T2[K]', 'T3[K]']
            
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Set default parameters if not provided
            t_add = parameters.get('t_add', 7380.0)
            adj_factor = parameters.get('adj_factor', [0.05, 10.0])
            t_span = parameters.get('t_span', [0.0, 13100.0])
            dt = parameters.get('dt', 1.0)
            
            # Set initial conditions
            y_0 = []
            
            # Get initial conditions from parameters or use defaults
            L_0i = parameters.get('L_0i', None)
            CVAM_r0i = parameters.get('CVAM_r0i', None)
            CBA_r0i = parameters.get('CBA_r0i', None)
            CNaPS_r0i = parameters.get('CNaPS_r0i', None)
            CTBHP_r0i = parameters.get('CTBHP_r0i', None)
            CCRD_r0i = parameters.get('CCRD_r0i', None)
            CMPOL_r0i = parameters.get('CMPOL_r0i', None)
            Np_r0i = parameters.get('Np_r0i', None)
            T1_0i = parameters.get('T1_0i', None)
            T3_0i = parameters.get('T3_0i', None)
            
            # If initial conditions not provided, we'll need to calculate them
            # For now, we'll use the original model's default calculation
            # This would need to be adapted based on your specific needs
            
            # Create Laboratory_process instance
            laboratory = Laboratory_process(t_add, adj_factor, data)
            
            # Run simulation
            t, sol = laboratory.Reactor_solver(t_span=t_span, dt=dt, y_0=y_0)
            
            if t is None or sol is None:
                raise RuntimeError("Simulation failed - no solution returned")
            
            # Extract results
            L = sol[:, 0]
            CVAM_1 = sol[:, 1]
            CBA_1 = sol[:, 2]
            CNaPS_1 = sol[:, 3]
            CTBHP_1 = sol[:, 4]
            CCRD_1 = sol[:, 5]
            CMPOL_1 = sol[:, 6]
            Np_I = sol[:, 7]
            T1 = sol[:, 8]
            T3 = sol[:, 9]
            
            # Calculate additional properties
            mu_I = laboratory.mu_POL(T1, CMPOL_1)
            
            # Prepare results for storage
            results = {
                'time': t.tolist(),
                'liquid_level': L.tolist(),
                'vam_concentration': CVAM_1.tolist(),
                'ba_concentration': CBA_1.tolist(),
                'naps_concentration': CNaPS_1.tolist(),
                'tbhp_concentration': CTBHP_1.tolist(),
                'crd_concentration': CCRD_1.tolist(),
                'polymer_concentration': CMPOL_1.tolist(),
                'particle_number': Np_I.tolist(),
                'reactor_temperature': T1.tolist(),
                'jacket_temperature': T3.tolist(),
                'viscosity': mu_I.tolist(),
                'heat_transfer_rate': laboratory.lists.Q1,
                'heat_transfer_coeff': laboratory.lists.U1
            }
            
            # Store results
            if not db.store_reactor_results(experiment['id'], results):
                raise RuntimeError("Failed to store results")
            
            # Update status to completed
            db.update_experiment_status(experiment['id'], 'completed')
            
            print(f"Experiment {experiment['id']} completed successfully")
            
        except Exception as e:
            error_message = str(e)
            print(f"Error processing experiment {experiment['id']}: {error_message}")
            
            # Increment try count
            db.increment_experiment_tries(experiment['id'])
            
            # Check if we've exceeded max tries
            if experiment['number_of_tries'] + 1 >= max_tries:
                # Mark as permanently failed
                db.mark_experiment_failed_permanently(experiment['id'], error_message)
                print(f"Experiment {experiment['id']} marked as permanently failed (exceeded {max_tries} tries)")
            else:
                # Reset to pending for retry
                db.update_experiment_status(experiment['id'], 'pending', error_message)
                print(f"Experiment {experiment['id']} reset to pending for retry (try {experiment['number_of_tries'] + 1}/{max_tries})")
    
    print(f"[{datetime.now()}] Experiment processing completed.")

if __name__ == '__main__':
    process_pending_experiments()