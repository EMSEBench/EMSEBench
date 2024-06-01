import pandas as pd
import subprocess

grid_search = [[384,0.000001,0.55,2],[384,0.0001,0.55,2],[384,0.000001,0.55,3],[384,0.000001,0.5,2],[384,0.000001,0.5,3],[576,0.000001,0.55,2],[192,0.000001,0.55,2],[384,0.0001,0.4,2],[384,0.000001,0.3,2],[384,0.000001,0.7,2]]

for hyperparameters in grid_search:
    #change this line/ command
    cur_cmd = "python GRU_tuning.py " + str(hyperparameters[0]) + " " + str(hyperparameters[1]) + " " + str(hyperparameters[2]) + " " + str(hyperparameters[3])
    cmd_output = subprocess.run(cur_cmd, stdout=subprocess.PIPE, text=True, shell=True).stdout
