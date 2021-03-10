from typing import List, Tuple
import math
import numpy as np
def sinusoid_regress(x, y) -> Tuple[int, int, int, int]:
    avg = sum(y)/len(y)
    stdev = (sum((yi-avg)**2 for yi in y)/len(y))**.5
    # to find period, clump the points together at amplitude intersection
    E = 1
    inx = [x[i] for i in range(len(x)) if abs(y[i]-avg+stdev) < E]
    # print('\n'.join(f"{x}\t4" for x in inx))

    min_period = 40000
    periods = [inx[i]-inx[i-1] for i in range(len(inx)) if inx[i]-inx[i-1] >= min_period]
    avg_period = np.mean(periods)
    freq = 1/avg_period
    # candidate phase shifts
    clamp = lambda x: -1 if x < -1 else 1 if x > 1 else x
    candidate_ps = [math.asin(clamp((y[i]-avg)/stdev))-(freq*2*3.1415)*x[i] for i in range(len(x))]

    def model(x, c):
        return stdev*math.sin(avg_period*x-c)+avg

    def r_squared(model, c):
        tss = sum((y[i] - c)**2 for i in range(len(x)))
        error = 1-sum((y[i]-model(x[i], c))**2 for i in range(len(x)))/tss
        return error
    # print(r_squared(model, min(candidate_ps, key = lambda c: abs(1-r_squared(model, c)))))
    # a*sin(bx-c)+d
    return stdev, avg_period, min(candidate_ps, key = lambda c: abs(1-r_squared(model, c))), avg