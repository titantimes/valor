from sql import ValorSQL
import matplotlib.pyplot as plt
import matplotlib.dates as md
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import MaxNLocator
import numpy as np
from datetime import datetime
from bisect import bisect_left
import time

PCSTART = 1791382431
PLAYER_COUNT_MAX_DISTANCE = 600


class NormalisationE(Exception):
    pass


def normaliser(times, counts, player_counts):
    sample_times = [row[0] for row in player_counts]
    normalized_times = []
    normalized_counts = []
    missing = 0
    for timestamp, count in zip(times, counts):
        index = bisect_left(sample_times, timestamp)
        candidates = player_counts[max(0, index - 1):index + 1]
        if not candidates:
            missing += 1
            continue
        sample_time, total = min(candidates, key=lambda row: abs(row[0] - timestamp))
        if abs(sample_time - timestamp) > PLAYER_COUNT_MAX_DISTANCE or total is None or total <= 0:
            missing += 1
            continue
        normalized_times.append(timestamp)
        normalized_counts.append(100 * count / total)
    return np.array(normalized_times), np.array(normalized_counts), missing


def check_normalized_sample_count(count, opt):
    remaining = count
    if opt.moving_average > 1:
        remaining -= opt.moving_average - 1
    if remaining < 1:
        raise NormalisationE("Not enough matched samples for the requested moving average.")
    if opt.smooth and remaining < 4:
        raise NormalisationE("At least four matched samples are needed to smooth the graph.")


def plot_process(lock, opt, query):
    a = []
    b = []
    xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')

    player_counts = []
    if opt.normalize:
        start = max(PCSTART, int(opt.plot_start_time) - PLAYER_COUNT_MAX_DISTANCE)
        end = int(opt.plot_end_time) + PLAYER_COUNT_MAX_DISTANCE
        with lock:
            player_counts = ValorSQL.execute_sync(
                f"SELECT time, count FROM player_count WHERE time >= {start} AND time <= {end} ORDER BY time ASC"
            )
        if not player_counts:
            raise NormalisationE("No online player totals are available for this range.")

    fig = plt.figure()
    fig.set_figwidth(20)
    fig.set_figheight(10)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(xfmt)
    plt.xticks(rotation=25)

    data_pts = 0
    missing = 0
    plotted = 0

    for name in opt.guild:
        with lock:
            res = ValorSQL.execute_sync(query % name)

        if opt.split:
            b = np.array([x[2] for x in res])
            a = np.array([x[1] for x in res])

            if opt.normalize:
                b, a, skipped = normaliser(b, a, player_counts)
                missing += skipped
                if not len(a):
                    data_pts += len(res)
                    continue
                plotted += len(a)
                check_normalized_sample_count(len(a), opt)

            if opt.moving_average > 1:
                a = np.convolve(a, np.ones(opt.moving_average)/opt.moving_average, mode="valid")
                b = b[:len(b)-opt.moving_average+1]

            if opt.smooth:
                spline = make_interp_spline(b, a)

                b = np.linspace(b.min(), b.max(), 500)
                a = spline(b)
                a = np.clip(a, 0, None)

            plt.plot([datetime.fromtimestamp(x) for x in b], a, label=name)
            plt.legend(loc="upper left")
        else:
            for i in range(len(res)):
                if i >= len(a):
                    a = np.append(a, 0)
                    b = np.append(b, res[i][2])
                a[i] += res[i][1]

            a = np.array(a)
            b = np.array(b)

        data_pts += len(res)


    content = "Plot"

    if opt.split:
        content = "Split graph"
    else:
        if opt.normalize:
            b, a, missing = normaliser(b, a, player_counts)
            plotted = len(a)
        if opt.normalize and not plotted:
            plt.close(fig)
            raise NormalisationE("No guild samples have a nearby valid online player total.")
        if opt.normalize:
            check_normalized_sample_count(len(a), opt)
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
            a = np.clip(a, 0, None)

        plt.plot([datetime.fromtimestamp(x) for x in b], a) 

    if opt.normalize:
        if not plotted:
            plt.close(fig)
            raise NormalisationE("No guild samples have a nearby valid online player total.")
        content += "\nValues are percentages of all online players."
        if missing:
            content += f"\nOmitted {missing:,} guild samples without a valid player total within 10 minutes."

    ax.xaxis.set_major_locator(MaxNLocator(30))

    plt.title("Online Player Activity")
    plt.ylabel("Percentage of online players (%)" if opt.normalize else "Player Count")
    plt.xlabel("Date Y-m-d H:M:S")

    fig.savefig("/tmp/valor_guild_plot.png")
    plt.close(fig)

    return data_pts, content
    
