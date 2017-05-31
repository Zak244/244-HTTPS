var sys = require('system'),
    fs = require('fs');

var INPUTFILE = "../utilities/alexa-top-5",
    OUTPUTFILE = "filtered-top-5";

var using_https = null,
    cur_url = "",
    has_HTTPS_redirect = false;

// Main Execution:
var sites = getSiteList();
process_site(false);


function getSiteList() {
    try {
        // Open file, read text as blob, split by line:
        var input_sites = fs.open(INPUTFILE, "r").read().match(/[^\r\n]+/g);
        var output_sites = [];
        
        // index,site  -->    site     (extract only site from each line)
        input_sites.forEach(function(val, index, arr){
            var site = val.split(',')[1];
            output_sites.push(site);
            output_sites.push(site);
            output_sites.push("www."+site);
            output_sites.push("www."+site);
        });
        return output_sites;
    } catch (e) {
        console.log("Error: Could not open file: " + INPUTFILE);
        phantom.exit(-1);
    }
}

function process_site(use_https) {
    if (sites.length == 0) {
        phantom.exit();
    } else {
        var site = sites.shift(),
            page = require('webpage').create();

        cur_url = site;
        page.onResourceReceived = detect_protocol;
        page.settings.resourceTimeout = 2000; //timeout is 2 seconds
        if(!use_https) {
            using_https = false;
            has_HTTPS_redirect = false;
            page.open("http://" + site, function(status) {
                console.log("http://" + site + " " + status + " ... Rediect: " + has_HTTPS_redirect);
                page.release();
                process_site(true);
            });
        } else {
            using_https = true;
            page.open("https://" + site, function(status) {
                console.log("https://" + site + " " + status);
                page.release();
                process_site(false);
            });
        }
    }
}

function detect_protocol(response) {
    // check if the resource is done downloading 
    if (response.stage !== "end") return;

    if (!using_https) {
        if (https_match(response.url)) {
            console.log("HTTPS REDIRECT");
            has_HTTPS_redirect = true;
        }
    }    
}

function https_match(url) {
    url = url.toLowerCase();
    if(url.indexOf("https://") != 0)
        return false;
    return strEndsWith(url, cur_url) || strEndsWith(url, cur_url+"/");
        
}

// strEndsWith Source: 
// http://rickyrosario.com/blog/javascript-startswith-and-endswith-implementation-for-strings/
function strEndsWith(str, suffix) {
    return str.match(suffix+"$")==suffix;
}

function onResourceTimeout() {
    console.log("TIMED OUT");
}