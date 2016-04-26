[![Build Status](https://travis-ci.org/clarete/emailverifier.svg?branch=master)](https://travis-ci.org/clarete/emailverifier)

# Email verifier

This small software verifies a list of email addresses. Here's how you
run it:

## Environment

    $ git clone git@github.com:clarete/emailverifier.git
    $ mkvirtualenv emailverifier
    $ pip install -r requirements.txt

## Run the program

    $ python main.py INPUT.txt OUTPUT.csv

The `INPUT` file is a text file cointaining one email address per
line. The `OUTPUT` file is a CSV report with 3 columns, the email
address, if the email is valid or not and the error string, present if
the validation didn't work.

## Run tests

    $ pip install -r development.txt
    $ nosetests

