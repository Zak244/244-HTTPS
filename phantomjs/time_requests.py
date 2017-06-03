import os
import sys
import logging
import argparse
import urlparse
import numpy
import pprint
import pickle
import subprocess
import multiprocessing
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.append('..')
from loader import PageResult
from phantomjs_loader import PhantomJSLoader


SUCCESS = 'SUCCESS'
FAILURE_TIMEOUT = 'FAILURE_TIMEOUT'
FAILURE_NO_HTTP = 'FAILURE_NO_HTTP'
FAILURE_NO_HTTPS = 'FAILURE_NO_HTTPS'
FAILURE_UNKNOWN = 'FAILURE_UNKNOWN'
FAILURE_NO_200 = 'FAILURE_NO_200'
FAILURE_ARITHMETIC = 'FAILURE_ARITHMETIC'
FAILURE_UNSET = 'FAILURE_UNSET'

class URLResult(object):
    '''Status for several trials over HTTP and HTTPS for a URL'''
    def __init__(self, status, url):
        self.status = status
        self.url = url
        self.http_times = []
        self.https_times = []
        self.http_sizes = []  # shouldn't be changing, but...
        self.https_sizes = [] # shouldn't be different, but...

    def add_http_result(self, result):
        if result.status == SUCCESS:
            self.http_times.append(result.time)
            self.http_sizes.append(result.size)

    def add_https_result(self, result):
        if result.status == SUCCESS:
            self.https_times.append(result.time)
            self.https_sizes.append(result.size)

    def _get_http_mean(self):
        return numpy.mean(self.http_times)
    http_mean = property(_get_http_mean)

    def _get_http_median(self):
        return numpy.median(self.http_times)
    http_median = property(_get_http_median)

    def _get_http_stddev(self):
        return numpy.std(self.http_times)
    http_stddev = property(_get_http_stddev)

    def _get_https_mean(self):
        return numpy.mean(self.https_times)
    https_mean = property(_get_https_mean)

    def _get_https_median(self):
        return numpy.median(self.https_times)
    https_median = property(_get_https_median)

    def _get_https_stddev(self):
        return numpy.std(self.https_times)
    https_stddev = property(_get_https_stddev)

    def _get_size(self):
        return self.http_sizes[0] if len(self.http_sizes) > 0 else None
    size = property(_get_size)

    def try_calc(self):
        try:
            # do the calculations just to make sure they don't throw error
            http_mean = numpy.mean(self.http_times)
            http_median = numpy.median(self.http_times)
            https_mean = numpy.mean(self.https_times)
            https_median = numpy.median(self.https_times)
            if not http_mean or\
               not http_median or\
               not https_mean or\
               not https_median:
                raise Exception()
        except Exception as e:
            logging.error('Error calculating stats for %s: %s', self.url, e)
            self.status = FAILURE_ARITHMETIC

    def __str__(self):
        return 'RESULT: < Status=%s\tHTTP/HTTPS Mean=%f/%f StdDev=%f/%f Median=%f/%f\tURL=%s >'\
            % (self.status, self.http_mean, self.https_mean, self.http_stddev,\
            self.https_stddev, self.http_median, self.https_median, self.url)
    def __repr__(self):
        return self.__str__()

def make_url(url, protocol, port=None):
    # make sure it's a complete URL to begin with, or urlparse can't parse it
    if '://' not in url:
        url = 'http://%s' % url
    comps = urlparse.urlparse(url)

    new_netloc = comps.netloc
    if port:
        new_netloc = new_netloc.split(':')[0]
        new_netloc = '%s:%s' % (new_netloc, port)

    new_comps = urlparse.ParseResult(scheme=protocol, netloc=new_netloc,\
        path=comps.path, params=comps.params, fragment=comps.fragment,\
        query=comps.query)

    return urlparse.urlunparse(new_comps)

def process_url(url):
    # numpy warnings are errors
    old_numpy_settings = numpy.seterr(all='raise')

    http_url = make_url(url, 'http')
    https_url = make_url(url, 'https')
    logging.debug('HTTP URL:  %s' % http_url)
    logging.debug('HTTPS URL: %s' % https_url)

    result = URLResult(SUCCESS, url)

    loader = PhantomJSLoader(outdir=args.outdir, num_trials=args.numtrials,\
        disable_local_cache=True, disable_network_cache=False,\
        timeout=args.timeout, full_page=True)

    # Load the pages;
    loader.load_pages([http_url, https_url])

    # Make sure the URL was accessible over both HTTP and HTTPS
    if loader.page_results[http_url].status == PageResult.FAILURE_NOT_ACCESSIBLE:
        logging.debug('The URL "%s" cannot be accessed over HTTP.' % url)
        return URLResult(FAILURE_NO_HTTP, url)
    if loader.page_results[https_url].status == PageResult.FAILURE_NOT_ACCESSIBLE:
        logging.debug('The URL "%s" cannot be accessed over HTTPS.' % url)
        return URLResult(FAILURE_NO_HTTPS, url)

    # grab the individual results and put them into a URLResult object
    for http_result in loader.load_results[http_url]:
        result.add_http_result(http_result)
    for https_result in loader.load_results[https_url]:
        result.add_https_result(https_result)
    result.try_calc()  # sets status to FAILURE_ARITHMETIC if there's a problem

    logging.info(result)
    return result

def plot_results(filename_to_results, filenames=None):
    # use the filenames list to make sure we process files in order
    # (so we can control the order of the series on the plot)
    if not filenames: filenames = filename_to_results.keys()

    filename_to_data = defaultdict(lambda: defaultdict(list))
    fraction_data = []
    absolute_data = []

    for filename in filenames:
        results = filename_to_results[filename]
        for r in results:
            if r.status == SUCCESS:
                filename_to_data[filename]['both_success'].append(r.url)

                filename_to_data[filename]['mean_percent_inflations'].append(r.https_mean / r.http_mean)
                filename_to_data[filename]['mean_absolute_inflations'].append(r.https_mean - r.http_mean)
                filename_to_data[filename]['median_percent_inflations'].append(r.https_median / r.http_median)
                filename_to_data[filename]['median_absolute_inflations'].append(r.https_median - r.http_median)
                if r.size:
                    filename_to_data[filename]['mean_percent_by_size'].append( (int(r.size)/1000.0, r.https_mean / r.http_mean, r.http_stddev) )
                    filename_to_data[filename]['mean_absolute_by_size'].append( (int(r.size)/1000.0, r.https_mean - r.http_mean, r.http_stddev) )
                    filename_to_data[filename]['mean_http_by_size'].append( (int(r.size)/1000.0, r.http_mean, r.http_stddev) )
                    filename_to_data[filename]['mean_https_by_size'].append( (int(r.size)/1000.0, r.https_mean, r.http_stddev) )
            elif r.status == FAILURE_NO_HTTP:
                filename_to_data[filename]['no_http'].append(r.url)
            elif r.status == FAILURE_NO_HTTPS:
                filename_to_data[filename]['no_https'].append(r.url)
            else:
                filename_to_data[filename]['other_error'].append(r.url)

        print '%i sites were accessible over both protocols' %\
            len(filename_to_data[filename]['both_success'])
        print '%i sites were not accessible over HTTP' %\
            len(filename_to_data[filename]['no_http'])
        print '%i sites were not accessible over HTTPS' %\
            len(filename_to_data[filename]['no_https'])
        print '%i sites were not accessible for other reasons' %\
            len(filename_to_data[filename]['other_error'])

        fraction_data.append(filename_to_data[filename]['mean_percent_inflations'])
        fraction_data.append(filename_to_data[filename]['median_percent_inflations'])

        absolute_data.append(numpy.array(filename_to_data[filename]['mean_absolute_inflations']))# * 1000)  # s -> ms
        absolute_data.append(numpy.array(filename_to_data[filename]['median_absolute_inflations']))# * 1000)  # s -> ms

    #create ratio plot
    plt.figure(0)
    fraction_means = numpy.sort(fraction_data[0])
    yvals = numpy.arange(len(fraction_means))/float(len(fraction_means))
    plt.scatter(fraction_means, yvals, label='Mean')

    fraction_medians = numpy.sort(fraction_data[1])
    yvals = numpy.arange(len(fraction_medians))/float(len(fraction_medians))
    plt.scatter(fraction_medians, yvals, label='Median')

    plt.xlabel('Load Time Ratio (HTTPS/HTTP)')
    plt.ylabel('CDF')
    plt.title('Figure 5a Replication: Load time ratio for top 500 sites')
    plt.legend()
    plt.savefig('ratio.png')

    #create absolute plot
    plt.figure(1)
    absolute_means = numpy.sort(absolute_data[0])
    yvals = numpy.arange(len(absolute_means))/float(len(absolute_means))
    plt.scatter(absolute_means, yvals, label='Mean')

    absolute_medians = numpy.sort(absolute_data[1])
    yvals = numpy.arange(len(absolute_medians))/float(len(absolute_medians))
    plt.scatter(absolute_medians, yvals, label='Median')

    plt.xlabel('Load Time Difference (HTTPS - HTTP) [seconds]')
    plt.ylabel('CDF')
    plt.title('Figure 5b Replication: Load time difference for top 500 sites')
    plt.legend()
    plt.savefig('difference.png')

def summarize_results(filename_to_results):
    for results in filename_to_results.values():
        for result in results:
            print result

def main():

    filename_to_results = {}
    filenames = []  # so we know the original order
    if args.readfile:
        for file in args.readfile:
            with open(file, 'r') as f:
                results = pickle.load(f)
                filename_to_results[file] = results
                filenames.append(file)
            f.closed
    else:
        if args.urlfile:
            with open(args.urlfile, 'r') as f:
                for line in f:
                    args.urls.append(line.strip())
            f.closed

        # process logs individually in separate processes
        pool = multiprocessing.Pool(args.numcores)
        try:
            results = pool.map_async(process_url, args.urls).get(0xFFFF)
        except KeyboardInterrupt:
            sys.exit()
        except multiprocessing.TimeoutError:
            logging.warn('Multiprocessing timeout')

        filename = os.path.join(args.outdir, '%s_fetcher.pickle'%args.tag)
        with open(filename, 'w') as f:
            pickle.dump(results, f)
        f.closed

        filename_to_results[filename] = results
        filenames.append(filename)

    if args.summary:
        summarize_results(filename_to_results)
    else:
        plot_results(filename_to_results, filenames)



if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Calculate difference in load time over HTTP and HTTPS.')
    parser.add_argument('urls', nargs='*', help='URLs of the objects to load. If object is HTML, sub-resources are *not* fetched unless the "-p" flag is supplied.')
    parser.add_argument('-f', '--urlfile', help='File containing list of URLs, one per line.')
    parser.add_argument('-r', '--readfile', nargs='+', help='Read previously pickled results instead of fetching URLs.')
    parser.add_argument('-y', '--summary', action='store_true', default=False, help='Show a summary of results instead of generating plots.')
    parser.add_argument('-n', '--numtrials', type=int, default=20, help='How many times to fetch each URL with each protocol.')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Timeout for requests, in seconds')
    parser.add_argument('-g', '--tag', help='Tag to prepend to output files')
    parser.add_argument('-o', '--outdir', default='.', help='Output directory (for plots, etc.)')
    parser.add_argument('-c', '--numcores', type=int, help='Number of cores to use.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help='only print errors')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='print debug info. --quiet wins if both are present')
    args = parser.parse_args()

    if not os.path.isdir(args.outdir):
        try:
            os.makedirs(args.outdir)
        except Exception as e:
            logging.error('Error making output directory: %s' % args.outdir)
            sys.exit(-1)

    # set up logging
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        format = "%(levelname) -10s %(asctime)s %(module)s:%(lineno) -7s %(message)s",
        level = level
    )


    main()
