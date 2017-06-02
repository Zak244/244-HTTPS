var sys = require('system'),
    fs = require('fs');

var INPUTFILE = "../utilities/alexa-top-500",
    OUTPUTFILE = "filtered-top-500";

var url_index = 0,
    use_https = false,
    iteration = 0;

// Main Execution:
var sites = getSiteList();
var results = {};
process_site(false);
/* Because of JS's asynchronous nature, all code beyond this should go in the 
   if() block of the process_site() function */

function getSiteList() {
    try {
        // Open file, read text as blob, split by line:
        var input_sites = fs.open(INPUTFILE, "r").read().match(/[^\r\n]+/g);
        var output_sites = [];
        
        // STATUS site  -->    site  if STATUS === OK
        input_sites.forEach(function(val, index, arr){
            var line = val.split(' ');
            if(line[0] === "OK") {
                output_sites.push(line[1]);
            }
        });
        return output_sites;
    } catch (e) {
        console.log("Error: Could not open file: " + INPUTFILE);
        phantom.exit(-1);
    }
}

function process_site(use_https) {
    /* Exit when we've tested all sites */
    if (url_index >= sites.length - 1) {
        /* "Callback" here: (executes when done with all page requests) */
        printResults();
        phantom.exit();
    } 

    
    else {
        var site = sites.shift(),
            page = require('webpage').create();

        cur_url = site;
        page.onResourceReceived = detect_protocol;
        page.settings.resourceTimeout = 10000; //timeout is 10 seconds
        page.onResourceTimeout = logTimeout;
        phantom.clearCookies(); //clear cookies every new request

        /* HTTP: */
        if(!use_https) {
            using_https = false;
            has_HTTPS_redirect = false;
            
            page.open("http://" + site, function(status) {
                console.log("http://" + site + " " + status + " ... Rediect: " + has_HTTPS_redirect);
                
                if(!(site in results)) 
                    results[site] = {};

                if(status === "success")
                    results[site].hasHTTP = !has_HTTPS_redirect;
                else
                    results[site].hasHTTP = false;

                page.release();
                process_site(true);
            });
        } 

        /* HTTPS: */
        else {
            using_https = true;
            page.open("https://" + site, function(status) {
                console.log("https://" + site + " " + status);
                
                if(!(site in results)) 
                    results[site] = {};
                
                /* Will return failure if HTTPS not enabled */
                results[site].hasHTTPS = (status === "success");
                

                page.release();
                process_site(false);
            });
        }
    }
}

function printResults() {
    var output = [];
    var n_OK = 0,
        n_RE = 0,
        n_NS = 0,
        n_ERROR = 0;

    for (var site in results) {
        if (results[site].hasHTTPS && results[site].hasHTTP) {
            output.push("OK "+site);
            n_OK ++;
        }
        else if(results[site].hasHTTPS && !results[site].hasHTTP) {
            output.push("RE "+site);
            n_RE ++;
        }
        else if(results[site].hasHTTP && !results[site].hasHTTPS) {
            output.push("NS "+site);
            n_NS ++;
        }
        else {
            output.push("ERROR "+site+"==========");
            n_ERROR ++;
        }
    }
    try {
        var n_total = n_OK + n_ERROR + n_NS + n_RE;
        var METADATA = "\r\nOK: "+n_OK+";   RE: "+n_RE+";   NS: "+n_NS+";   ERROR: "+n_ERROR+";   TOTAL: "+n_total+";";
        fs.write(OUTPUTFILE, output.join('\r\n')+METADATA, 'w');
    } catch (e) {
        console.log("COULD NOT WRITE TO OUTPUT FILE");
        phantom.exit(-1);
    }
}

function logTimeout() {
    console.log("TIMED OUT");
}