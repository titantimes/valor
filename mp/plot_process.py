from sql import ValorSQL
from util import guild_name_from_tag
import matplotlib.pyplot as plt
import matplotlib.dates as md
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import MaxNLocator
import numpy as np
from datetime import datetime
import time

def plot_process(lock, opt, query):
    a = []
    b = []
    xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')

    fig = plt.figure()
    fig.set_figwidth(20)
    fig.set_figheight(10)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(xfmt)
    plt.xticks(rotation=25)

    data_pts = 0

    for name in opt.guild:
        with lock:
            res = ValorSQL.execute_sync(query % name)

        if opt.split:
            b = np.array([x[2] for x in res])
            a = np.array([x[1] for x in res])

            if opt.moving_average > 1:
                a = np.convolve(a, np.ones(opt.moving_average)/opt.moving_average, mode="valid")
                b = b[:len(b)-opt.moving_average+1]

            if opt.smooth:
                spline = make_interp_spline(b, a)

                b = np.linspace(b.min(), b.max(), 500)
                a = spline(b)

            plt.plot([datetime.fromtimestamp(x) for x in b], a, label=guild)
            plt.legend(loc="upper left")

        else:
            for i in range(len(res)):
                if i >= len(a):
                    a.append(0)
                    b.append(res[i][2])
                a[i] += res[i][1]

            a = np.array(a)
            b = np.array(b)

        data_pts += len(res)


    content = "Plot"

    if opt.split:
        content = "Split graph"
    else:
        content =f"""```
Mean: {sum(a)/len(a):.7}
Max: {max(a)}
Min: {min(a)}```"""
        if opt.moving_average > 1:
            a = np.convolve(a, np.ones(opt.moving_average)/opt.moving_average, mode="valid")
            b = b[:len(b)-opt.moving_average+1]

        if opt.smooth:
            spline = make_interp_spline(b, a)

            b = np.linspace(b.min(), b.max(), 500)
            a = spline(b)

        plt.plot([datetime.fromtimestamp(x) for x in b], a) 

    ax.xaxis.set_major_locator(MaxNLocator(30))

    plt.title("Online Player Activity")
    plt.ylabel("Player Count")
    plt.xlabel("Date Y-m-d H:M:S")

    fig.savefig("/tmp/valor_guild_plot.png")

    return data_pts, content
    
