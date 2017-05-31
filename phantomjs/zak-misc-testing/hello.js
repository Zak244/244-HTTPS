var page = require('webpage').create(),
	sys = require('system'),
	resources = [];

var url = "http://hellopoetry.com";


page.open(url, function(status){
	for (var i in resources)
		console.log(resources[i].redirectURL);
	// console.log("Statuses: ", statuses);
	console.log(JSON.stringify(resources, null, 4));
	phantom.exit();
});












// Get Status Code:
// http://stackoverflow.com/questions/30221204/how-can-i-see-the-http-status-code-from-the-request-made-by-page-open
page.onResourceReceived = function(response) {
    // check if the resource is done downloading 
    if (response.stage !== "end") return;
    // apply resource filter if needed:
    if (response.headers.filter(function(header) {
        if (header.name == 'Content-Type' && header.value.indexOf('text/html') == 0) {
            return true;
        }
        return false;
    }).length > 0)
        resources.push(response);
};
