#!/bin/sh
#SBATCH --job-name=automated-phenology-forecast # Job name
#SBATCH --cpus-per-task=2 #  
#SBATCH --nodes=1 #Number of nodes
#SBATCH --ntasks=1 #
#SBATCH --mem=48gb # Memory per processor
#SBATCH --time=24:00:00 # Time limit hrs:min:sec
#SBATCH --qos=ewhite
#SBATCH --partition=hpg2-compute
#SBATCH --output=logs/automated_phenology_forecast.out

# Load conda environment
source activate phenology_forecasts

cd phenology_forecasts
python3 generate_phenology_forecasts.py
