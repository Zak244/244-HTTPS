console.log("Running timer....");
var sys = require('system'),
    fs = require('fs');

// Configurable Global Constants:
/* The timeout */
var NTRIALS = 20,
    T_TIMEOUT = 5000,  
    INPUTFILE = "filtered-top-20",
    OUTPUTFILE = "measurements-top-20-20";

// Dynamic Globals:
var url_index = 0,
    use_https = false,
    iteration = 0,
    time_start = null;

// Main Execution:
console.log("Going to get site list");
var sites = getSiteList();
console.log("Got site list");
var results = {};
console.log("Running test...");
process_site(false);
/* Because of JS's asynchronous nature, all code logically executed after this 
    should go in the if() block of the process_site() function */

function getSiteList() {
    try {
        // Open file, read text as blob, split by line:
        var input_sites = fs.open(INPUTFILE, "r").read().match(/[^\r\n]+/g);
        var output_sites = [];
        
        // index,site  -->    site     (extract only site from each line)
        input_sites.forEach(function(val, index, arr){
            var line = val.split(' ');
            if(line[0] === "OK")
                output_sites.push(line[1]);
        });

        console.log("Testing load times of "+output_sites.length+" pages over HTTP and HTTPS.");
        return output_sites;
    } catch (e) {
        console.log("Error: Could not open file: " + INPUTFILE);
        phantom.exit(-1);
    }
}


function whenLoaded(status, page) {
    var total_time = Date.now() - time_start;

    if(!(site in results)) {
        results[site] = {
            "HTTP": {}, 
            "HTTPS": {}
        };
    }

    if (use_https) {
        results[site]["HTTPS"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
        console.log("Load "+iteration+": "+results[site]["HTTPS"][iteration]);
    }
    else {
        results[site]["HTTP"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
        console.log("Load "+iteration+": "+results[site]["HTTP"][iteration]);
    }

    /* Update iteration */
    iteration++;

    page.release();
    process_site();
}

function process_site() {
    if (url_index >= sites.length) {
        console.log("Finished loading all sites. Now processing timing data...");
        /* "Callback" here: (executes when done with all page requests) */
        printResults();
        phantom.exit();
    } else {
        /*Advance url index if necessary: */
        if (iteration == NTRIALS) {
            // Advance the index and switch to HTTP if just finished the HTTPS tests
            if (use_https) {
                url_index ++;
                use_https = false;
                if (url_index >= sites.length) {
                    console.log("Finished loading all sites. Now processing timing data...");
                    /* "Callback" here: (executes when done with all page requests) */
                    printResults();
                    phantom.exit();
                }
            }
            // Start doing HTTPS tests if just finished the HTTP tests
            else
                use_https = true;
            iteration = 0;
        }

        var site = sites[url_index],
            page = require('webpage').create();

        /* Set page parameters: */
        page.settings.resourceTimeout = T_TIMEOUT; //timeout is 10 seconds
        page.onResourceTimeout = logTimeout;
        phantom.clearCookies(); //clear cookies every new request


        /* HTTP: */
        if(!use_https) {
            // If Starting new page: 
            if (iteration == 0) 
                console.log("Loading page "+(url_index+1)+" / "+sites.length+" over HTTP: "+sites[url_index]);

            // Start timer before loading page: 
            time_start = Date.now();
            // console.log("Opening http://"+site);
            page.open("http://" + site, function(status){
                var total_time = Date.now() - time_start;

                if(!(site in results)) {
                    results[site] = {
                        "HTTP": {}, 
                        "HTTPS": {}
                    };
                }

                if (use_https) {
                    results[site]["HTTPS"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
                    console.log("Load "+iteration+": "+results[site]["HTTPS"][iteration]);
                }
                else {
                    results[site]["HTTP"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
                    console.log("Load "+iteration+": "+results[site]["HTTP"][iteration]);
                }

                /* Update iteration */
                iteration++;

                page.release();
                process_site();
            });
        } 

        /* HTTPS: */
        else {
            // If Starting new page: 
            if (iteration == 0)
                console.log("Over HTTPS: ");
            
            time_start = Date.now();
            // console.log("Opening https://"+site);
            page.open("https://" + site, function(status){
                var total_time = Date.now() - time_start;

                if(!(site in results)) {
                    results[site] = {
                        "HTTP": {}, 
                        "HTTPS": {}
                    };
                }

                if (use_https) {
                    results[site]["HTTPS"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
                    console.log("Load "+iteration+": "+results[site]["HTTPS"][iteration]);
                }
                else {
                    results[site]["HTTP"][iteration] = (status === "success") ? total_time : "ERROR:NOLOAD";
                    console.log("Load "+iteration+": "+results[site]["HTTP"][iteration]);
                }

                /* Update iteration */
                iteration++;

                page.release();
                process_site();
            });
        }
    }
}


function printResults() {
    var output = [];
    for (var site in results) {
        // HTTP Stuff:
        var HTTP_data = results[site]["HTTP"];
        if(hasError(HTTP_data)){
            console.log(site+" HAS HTTP ERROR, SKIPPING");
            continue;
        }
        var HTTP_line = site+" HTTP ";
        for(var trial in HTTP_data) {
             HTTP_line += msToStr(HTTP_data[trial])+" ";
        }
        var HTTP_median = calcMedian(HTTP_data);
        var HTTP_mean = calcMean(HTTP_data);
        HTTP_line += " Med "+msToStr(HTTP_median)+" Avg "+msToStr(HTTP_mean);
        console.log(HTTP_line);

        // HTTPS Stuff 
        var HTTPS_data = results[site]["HTTPS"];
        if(hasError(HTTPS_data)){
            console.log(site+" HAS HTTPS ERROR, SKIPPING");
            continue;
        }
        var HTTPS_line = site+" HTTPS ";
        for (var trial in HTTPS_data) {
             HTTPS_line += msToStr(HTTPS_data[trial])+" ";
        }
        var HTTPS_median = calcMedian(HTTPS_data);
        var HTTPS_mean = calcMean(HTTPS_data);
        HTTPS_line += " Med "+msToStr(HTTPS_median)+" Avg "+msToStr(HTTPS_mean);
        console.log(HTTPS_line);

        // Comparison Stuff:
        var ratio_median = HTTPS_median / HTTP_median;
        var ratio_mean   = HTTPS_mean   / HTTP_mean;
        var diff_median  = HTTPS_median - HTTP_median;
        var diff_mean    = HTTPS_mean   - HTTP_mean; 

        var comp_line = site+" COMP "+ratio_median.toPrecision(4)+" "+msToStr(diff_median)+" "+ratio_mean.toPrecision(4)+" "+msToStr(diff_mean);
        console.log(comp_line);

        output.push(HTTP_line);
        output.push(HTTPS_line);
        output.push(comp_line);
    }
    try {
        fs.write(OUTPUTFILE, output.join('\r\n'), 'w');
    } catch (e) {
        console.log("COULD NOT WRITE TO OUTPUT FILE");
        phantom.exit(-1);
    }
}

function hasError(data) {
    for (var i in data) {
        if (data[i] === "ERROR:NOLOAD")
            return true;
    }
    return false;
}

// Assumes data array length 4
function calcMedian(data) {
    var sorted = [];
    for (var i in data) {
        sorted.push(data[i]);
    }
    sorted = sorted.sort(function(a,b){
        return a-b;
    });
    return (sorted[Math.floor((NTRIALS-1)/2.0)] + sorted[Math.floor((NTRIALS-1)/2.0)])/2.0;
}

// Assumes data array length 4
function calcMean(data) {
    var sum = 0;
    for (var i in data) {
        sum += data[i];
    }
    return (sum * 1.0) / NTRIALS;
}

function msToStr(ms) {
    var seconds = Math.round(ms) / 1000;
    return ""+seconds;
}

function logTimeout() {
    console.log("TIMED OUT");
}