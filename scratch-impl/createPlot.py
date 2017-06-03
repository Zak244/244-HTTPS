import numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA_INPUT_FILE = "final-data-500"

def convert_data(filepath):
    with open(filepath) as f:
        fraction_data = [[], []]
        absolute_data = [[], []]
        raw_lines = [x.strip() for x in f.readlines()]
        for line in raw_lines:
            site, _, frac_med, diff_med, frac_avg, diff_avg = line.split(" ")
            fraction_data[0].append(frac_avg)
            fraction_data[1].append(frac_med)
            absolute_data[0].append(diff_avg)
            absolute_data[1].append(diff_med)
        return fraction_data, absolute_data

def plot_data(fraction_data, absolute_data):
    #create ratio plot
    plt.figure(0)
    fraction_means = [float(x) for x in numpy.sort(fraction_data[0])]
    yvals = numpy.arange(len(fraction_means))/float(len(fraction_means))
    plt.scatter(fraction_means, yvals, label='Mean')

    fraction_medians = [float(x) for x in numpy.sort(fraction_data[1])]
    yvals = numpy.arange(len(fraction_medians))/float(len(fraction_medians))
    plt.scatter(fraction_medians, yvals, label='Median')

    plt.xlabel('Load Time Ratio (HTTPS/HTTP)')
    plt.ylabel('CDF')
    plt.title('Figure 5a Replication: Load time ratio for top 500 sites over fiber')
    plt.legend()
    plt.savefig('scratch-ratio.png')

    #create absolute plot
    plt.figure(1)
    absolute_means = numpy.sort([float(x) for x in absolute_data[0]])
    print(absolute_means)
    yvals = numpy.arange(len(absolute_means))/float(len(absolute_means))
    plt.scatter(absolute_means, yvals, label='Mean')

    absolute_medians = numpy.sort([float(x) for x in absolute_data[1]])
    yvals = numpy.arange(len(absolute_medians))/float(len(absolute_medians))
    plt.scatter(absolute_medians, yvals, label='Median')

    plt.xlabel('Load Time Difference (HTTPS - HTTP) [seconds]')
    plt.ylabel('CDF')
    plt.title('Figure 5b Replication: Load time difference for top 500 sites over fiber')
    plt.legend()
    plt.savefig('scratch-difference.png')

if __name__ == "__main__":
    fraction_data, absolute_data = convert_data(DATA_INPUT_FILE)
    plot_data(fraction_data, absolute_data)