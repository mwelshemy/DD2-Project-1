import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

input_transitions = [0.0100, 0.0231, 0.0531, 0.1225, 0.2823, 0.6507, 1.5000]
load_capacitances = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]

my_cells = [
    "invx1",
    "invx2",
    "invx4",
    "invx8",
    "nand2x1",
    "nand2x2",
    "nand2x4",
    "nor2x1",
    "nor2x2",
    "nor2x4",
    "maj3x1",
    "maj3x2",
    "maj3x4",
]


def simulate_cell(args):
    cell_name, c_load_pf, slew_ns, sim_id = args
    filename = f"sim_temp_{sim_id}.spice"

    spice_code = f"""testbench
.include cells.spice
.lib "/path/to/sky130.lib.spice" tt
.temp 25

VDD VDD 0 1.8
VIN IN 0 PULSE(0 1.8 1n {slew_ns}n {slew_ns}n 6n 15n)

X_DUT IN IN IN OUT VDD 0 {cell_name}
CLOAD OUT 0 {c_load_pf}p

.tran 1p 20n

.control
run
meas tran cell_rise trig v(IN) val=0.9 fall=1 targ v(OUT) val=0.9 rise=1
meas tran cell_fall trig v(IN) val=0.9 rise=1 targ v(OUT) val=0.9 fall=1
meas tran rise_transition trig v(OUT) val=0.36 rise=1 targ v(OUT) val=1.44 rise=1
meas tran fall_transition trig v(OUT) val=1.44 fall=1 targ v(OUT) val=0.36 fall=1
print cell_rise cell_fall rise_transition fall_transition
quit
.endc
.end
"""
    if "inv" in cell_name:
        spice_code = spice_code.replace(
            "X_DUT IN IN IN OUT VDD 0", "X_DUT IN OUT VDD 0"
        )
    elif "nand" in cell_name or "nor" in cell_name:
        spice_code = spice_code.replace(
            "X_DUT IN IN IN OUT VDD 0", "X_DUT IN IN OUT VDD 0"
        )

    with open(filename, "w") as f:
        f.write(spice_code)

    result = subprocess.run(["ngspice", "-b", filename], capture_output=True, text=True)

    if os.path.exists(filename):
        os.remove(filename)

    results = {"cell": cell_name, "load": c_load_pf, "slew": slew_ns}
    for line in result.stdout.split("\n"):
        if (
            line.startswith("cell_rise =")
            or line.startswith("cell_fall =")
            or line.startswith("rise_transition =")
            or line.startswith("fall_transition =")
        ):
            parts = line.split("=")
            results[parts[0].strip()] = float(parts[1].strip())

    print(f"Completed {cell_name} | Slew: {slew_ns}ns | Load: {c_load_pf}pF")
    return results


tasks = []
sim_id = 0
for cell in my_cells:
    for slew in input_transitions:
        for load in load_capacitances:
            tasks.append((cell, load, slew, sim_id))
            sim_id += 1

max_threads = os.cpu_count() or 4
print(f"Starting {len(tasks)} simulations using {max_threads} CPU threads:")
all_results = []

with ThreadPoolExecutor(max_workers=max_threads) as executor:
    futures = [executor.submit(simulate_cell, task) for task in tasks]
    for future in as_completed(futures):
        all_results.append(future.result())

print("\nSimulations complete! Formatting NLDM matrices:")

with open("nldm_tables.csv", "w") as f:
    for cell in my_cells:
        cell_data = [r for r in all_results if r["cell"] == cell]
        matrices = {
            "cell_rise": [],
            "cell_fall": [],
            "rise_transition": [],
            "fall_transition": [],
        }

        for slew in input_transitions:
            row_rise, row_fall, row_rtrans, row_ftrans = [], [], [], []
            for load in load_capacitances:
                data = next(
                    (r for r in cell_data if r["slew"] == slew and r["load"] == load),
                    {},
                )
                row_rise.append(f"{data.get('cell_rise',0)*1e9:.5f}")
                row_fall.append(f"{data.get('cell_fall',0)*1e9:.5f}")
                row_rtrans.append(f"{data.get('rise_transition',0)*1e9:.5f}")
                row_ftrans.append(f"{data.get('fall_transition',0)*1e9:.5f}")
            matrices["cell_rise"].append(row_rise)
            matrices["cell_fall"].append(row_fall)
            matrices["rise_transition"].append(row_rtrans)
            matrices["fall_transition"].append(row_ftrans)

        for param, matrix in matrices.items():
            f.write(f"\n{cell} - {param} (ns)\n")
            f.write(
                "Slew \\ Load," + ",".join([str(l) for l in load_capacitances]) + "\n"
            )
            for i, row in enumerate(matrix):
                f.write(f"{input_transitions[i]}," + ",".join(row) + "\n")

print("DONE! Check nldm_tables.csv")
