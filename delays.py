import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

input_transitions = [0.0100, 0.0231, 0.0531, 0.1225, 0.2823, 0.6507, 1.5000]  # ns
load_caps = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]  # pF
VDD = 1.8

cells = ["nor2x1", "nor2x2", "nor2x4",
         "maj3x1", "maj3x2", "maj3x4"]

#Function to generate Spice netlist for each simulation
def generate_spice(cell_name, slew_ns, c_load_pf):
    if "nor2" in cell_name:
        sources = f"""
VIN A 0 PULSE(0 {VDD} 0 {slew_ns}n {slew_ns}n 2n 6n)
V_B B 0 PULSE({VDD} 0 0 0 0 2n 4n)
X1 A B OUT VDD 0 {cell_name}
"""
    elif "maj3" in cell_name:
        sources = f"""
VIN A 0 PULSE(0 {VDD} 0 {slew_ns}n {slew_ns}n 2n 6n)
V_B B 0 PULSE({VDD} 0 0 0 0 2n 4n)
V_C C 0 {VDD}
X1 A B C OUT VDD 0 {cell_name}
"""
    else:
        sources = f"""
VIN A 0 PULSE(0 {VDD} 0 {slew_ns}n {slew_ns}n 2n 6n)
X1 A OUT VDD 0 {cell_name}
"""
    netlist = f"""
.include "cells2.spice"
VDD VDD 0 {VDD}

{sources}

Cload OUT 0 {c_load_pf}p

.tran 5p 10n

.control
run
meas tran cell_rise trig v(A) val={0.5*VDD} rise=1 targ v(OUT) val={0.5*VDD} rise=1
meas tran cell_fall trig v(A) val={0.5*VDD} fall=1 targ v(OUT) val={0.5*VDD} fall=1
meas tran rise_transition trig v(OUT) val={0.2*VDD} rise=1 targ v(OUT) val={0.8*VDD} rise=1
meas tran fall_transition trig v(OUT) val={0.8*VDD} fall=1 targ v(OUT) val={0.2*VDD} fall=1
print cell_rise cell_fall rise_transition fall_transition
quit
.endc
.end
"""
    return netlist

#Function that runs each simulation
def simulate_cell(args):
    cell_name, slew_ns, c_load_pf, sim_id = args
    filename = f"sim_temp_{sim_id}.spice"

    with open(filename, "w") as f:
        f.write(generate_spice(cell_name, slew_ns, c_load_pf))

    result = subprocess.run(["ngspice", "-b", filename],
                            capture_output=True, text=True)
    if os.path.exists(filename):
        os.remove(filename)

    data = {'cell': cell_name, 'slew': slew_ns, 'load': c_load_pf,
            'cell_rise': 0, 'cell_fall': 0, 'rise_transition': 0, 'fall_transition': 0}

    #Parser since extra text gave us an error
    for line in result.stdout.splitlines():
        line = line.strip()
        if '=' in line:
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().split()[0] 
            try:
                data[key] = float(val)
            except:
                data[key] = 0

    print(f"[{sim_id+1}] Completed {cell_name} | Slew={slew_ns}ns | Load={c_load_pf}pF")
    return data

tasks = []
sim_id = 0
for cell in cells:
    for slew in input_transitions:
        for load in load_caps:
            tasks.append((cell, slew, load, sim_id))
            sim_id += 1

print(f"Starting {len(tasks)} simulations...")

#This part is to speed up instead of waiting for each simulation to finish
all_results = []
from concurrent.futures import ThreadPoolExecutor, as_completed
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(simulate_cell, task) for task in tasks]
    for future in as_completed(futures):
        all_results.append(future.result())

#Filling the CSV with the delays
with open("nldm_delays_tables.csv", "w") as f:
    for cell in cells:
        f.write(f"\n\n{cell} NLDM Tables (ns)\n")
        f.write("Slew \\ Load," + ",".join([str(l) for l in load_caps]) + "\n")

        cell_data = [r for r in all_results if r['cell'] == cell]

        for param in ['cell_rise', 'cell_fall', 'rise_transition', 'fall_transition']:
            f.write(f"\n{param}\n")
            for slew in input_transitions:
                row = []
                for load in load_caps:
                    entry = next((r[param]*1e9 for r in cell_data if r['slew']==slew and r['load']==load), 0)
                    row.append(f"{entry:.5f}")
                f.write(f"{slew}," + ",".join(row) + "\n")

print("Execution done, Results are in 'nldm_delay_tables.csv'")
