import matplotlib.pyplot as plt

loads = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]
inverters = ['invx1', 'invx2', 'invx4', 'invx8']

# Read the CSV you just generated
with open('nldm_tables.csv', 'r') as f:
    lines = f.readlines()

rise_data = {inv: [] for inv in inverters}
fall_data = {inv: [] for inv in inverters}

current_cell = ""
current_param = ""

# Parse the text to find the 0.1225ns row for the inverters
for line in lines:
    line = line.strip()
    if " - " in line and "(ns)" in line:
        parts = line.split(" - ")
        current_cell = parts[0].strip()
        current_param = parts[1].replace("(ns)", "").strip()
    elif line.startswith("0.1225,"):
        if current_cell in inverters:
            vals = [float(x) for x in line.split(",")[1:]]
            if current_param == "cell_rise":
                rise_data[current_cell] = vals
            elif current_param == "cell_fall":
                fall_data[current_cell] = vals

# Draw the plot
plt.figure(figsize=(8, 6))
for inv in inverters:
    # Average delay = (rise_delay + fall_delay) / 2
    avg_delay = [(r + f) / 2.0 for r, f in zip(rise_data[inv], fall_data[inv])]
    plt.plot(loads, avg_delay, marker='o', label=inv)

plt.title('Delay vs. Load for Inverters (t_in = 0.1225ns)')
plt.xlabel('Load Capacitance (pF)')
plt.ylabel('Average Propagation Delay (ns)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()

# Save the image
plt.savefig('delay_vs_load.png', dpi=300)
print("SUCCESS: Plot saved as delay_vs_load.png!")
