# 244-Project 3:
## The cost of the S in HTTPS
A reproduction of select results of a 2014 paper

#Instructions

## 1. Setup Python Virtual Environment
`pip install virtualenv`

`virtualenv venv`

`source venv/bin/activate`

## 2. Install python dependancies
`pip install -r requirements.txt`

## 3. Add PhantomJS (depends on your OS)
Download [here](http://phantomjs.org/download.html), find and rename the
executable as `phantom`,then place executable in the `/phantomjs` directory.  

## 4. Run the tests
`./run_tests` (currently only tests that it can reach google.com)

After completion, plots should be available in root directory as `ratio.png`
and  `difference.png`.

## 5. To exit Virtual Environment
`deactivate`
