# VLSI Project 1: Standard Cell Characterization

## Team Members

* \[Mohamed] - Inverter \& NAND2 families
* \[Karim] - NOR2 \& MAJ3 families

## Repository Contents

* `cells.spice`: The SPICE netlists for all characterized standard cells.
* `characterize.py`: The multithreaded Python automation script.
* `nldm\_tables.csv`: The generated 7x7 delay and transition matrices.
* `Characterization\_Report.pdf`: Our final analytical report and plots.

## How to Run the Automation

To regenerate the NLDM tables, ensure you are on a Linux system with `ngspice` installed and run:
`python characterize.py`

