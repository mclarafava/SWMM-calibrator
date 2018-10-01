# SWMM-calibrator
# swmm-calibrator
A simple SWMM calibrator based on swmm5 package.

root folder
|_ data_dir
|_ model_dir
|_ results_dir

- model dir: INP file and .DAT files
- data_dir: field data
- results_dir: results will be saved here

# How to run
## 1. Install the dependencies

## 2. Configure the calibration parameters
Create a ini file (open saocarlos.ini as a example).
We are working on the documentation.
Hopefully, the name of each parameter will be self-explanatory.
-------
OBS: Use comma to separate each value and don't use spaces!
-------
## 3. Run the calibrator
python calibration.py
