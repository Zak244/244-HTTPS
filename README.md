# 244-Project 3:
## The cost of the S in HTTPS
A reproduction of select results of a 2014 paper

# Easy Instructions
Compatible with 64-bit Linux. We recommend running this inside of the CS244 VM.
## 1. Setup Testing Environment
`./setup`  

## 2. Run the tests
Warning: This will take several hours!
`./run_tests` 

After completion, plots should be available in root directory as `ratio.png`
and  `difference.png`.

# Alternate Instructions
The above reproduction scripts use the original author's scripts since they are more user friendly. However, if you are intrested in reproducing the measurements we published in our blog post, instructions and explanations are below:

### 1. Run the timing test:
Warning: this will take several hours!

This will overwrite the measurements-top-500 file. This relies on the existence of the filtered-top-500 file in the scratch-impl folder as well.

`cd scratch-impl`

`../phantomjs/phantom timePages.js`

### 2. Filter Out Extra Data
The timing script generates more data than is necessary to draw the CDF's, which could be used for additional analysis. The plotting script expects only a subsection of this data though:
`grep "COMP" measurements-top-500 > final-data-500`

### 3. Download Dependencies
From the root:

`cd utilities`

`pip install -r requirements.txt`

If the pip installer does not work, try manualling installing the dependencies listed in requirements.txt. You can ignore "requests" as it is not used by the plotting script.

### 4. Plot the results
From the root:

`cd scratch-impl`

`python createPlot.py`

If you run into any problems with setup, please email zakwhitt at stanford.edu or bencase at stanford.edu.