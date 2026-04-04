import matplotlib.pyplot as plt

target_slew = '0.1225'
inverters = ['invx1', 'invx2', 'invx4', 'invx8']
loads = [0.0005, 0.0013, 0.0035, 0.0094, 0.0249, 0.0662, 0.1758]

delays = {inv: [] for inv in inverters}

with open('nldm_tables.csv', 'r') as f:
    lines = f.readlines()

current_cell = ""
current_param = ""

for line in lines:
    line = line.strip()
    if not line: 
        continue
    
    if " - " in line and "(ns)" in line:
        parts = line.split(" - ")
        current_cell = parts[0]
        current_param = parts[1].replace(" (ns)", "")
        continue
        
    if current_cell in inverters and current_param == "cell_fall":
        if line.startswith(target_slew):
            values = line.split(',')[1:]
            delays[current_cell] = [float(v) for v in values]

plt.figure(figsize=(10, 6))
for inv in inverters:
    plt.plot(loads, delays[inv], marker='o', linewidth=2, label=inv)

plt.title('Propagation Delay vs. Load Capacitance (Input Transition = 0.1225ns)')
plt.xlabel('Load Capacitance (pF)')
plt.ylabel('Delay (ns)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)

# Save the graph as an image
plt.savefig('inverter_delay_plot.png', bbox_inches='tight')
print("SUCCESS! Saved as inverter_delay_plot.png")