# 500-Bus Power System Simulation Tool

A Python-based tool for simulating power system dynamics and analyzing fault responses in a 500-bus power system model.

## Overview

This repository contains two main scripts for power system simulation using PSS/E (Power System Simulator for Engineering):

- `func_500bus.py`: Core functions for bus identification, simulation execution, and result processing
- `main_func_500bus.py`: Main script for running batch simulations and data processing

The tools allow users to simulate different types of faults (bus faults, line faults, branch trips) and analyze the system's dynamic response through various electrical parameters.

## Features

- Identify buses by zone, neighbors, and generator buses
- Simulate three types of faults:
  - Bus faults
  - Line faults
  - Branch trips (with automatic reclosing)
- Collect and process key electrical parameters:
  - Active power (P)
  - Reactive power (Q)
  - Voltage (V)
  - Frequency (F)
- Deduplicate and merge simulation results for analysis
- Batch processing of multiple branch faults

## Dependencies

- Python 3.x
- PSS/E 33 (Power System Simulator for Engineering)
- pandas
- matplotlib
- dyntools (included with PSS/E)

## Installation

1. Ensure PSS/E 33 is installed on your system
2. Clone this repository:
   ```
   git clone https://github.com/yourusername/500bus-simulation.git
   cd 500bus-simulation
   ```
3. Install required Python packages:
   ```
   pip install pandas matplotlib
   ```
4. Verify PSS/E path in `func_500bus.py`:
   ```python
   PSSE_BIN_PATH = r'C:\Program Files (x86)\PTI\PSSE33\PSSBIN'
   ```
   Update this path if your PSS/E installation is in a different location.

## Usage

### Basic Simulation

1. Prepare your RAW (static data) and DYR (dynamic data) files
2. Modify parameters in `main_func_500bus.py` as needed:
   - Fault start/clear times
   - Simulation end time
   - Observation bus list
   - Output file paths
3. Run the main script:
   ```
   python main_func_500bus.py
   ```

### Key Functions

- `get_busid()`: Retrieve bus information based on different criteria
- `run_once()`: Execute a single simulation with specified fault parameters
- `get_out_data()`: Process simulation output files into structured data
- `deduplicate_powr_columns()` & `deduplicate_qpower_columns()`: Remove redundant columns from results

## Output

Simulation results are saved as CSV files containing:
- Time-series data of active power (P)
- Time-series data of reactive power (Q)
- Time-series data of voltage (V)
- Time-series data of frequency (F)

## Notes

- The example uses the ACTIVSg500 test system (RAW and DYR files not included)
- Adjust the `PSSE_BIN_PATH` in `func_500bus.py` to match your PSS/E installation
- Simulation times can be long depending on the system size and simulation duration
- The batch processing in `main_func_500bus.py` is currently set to process branches 2-19 (modify the range for different branches)
