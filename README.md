Python Guerrillamail
====================

Python Guerrillamail is a Python client API and command line interface for
interacting with a `Guerrillamail` temporary email server.

This package was forked from `ncjones/python-guerrillamail` and builds by adding functionality for forgetting an address from the session as well as an additional client function for deleted individual emails via their `guid`. 

Installation
------------
     pip install https://github.com/samjtozer/python-guerrillamail.git


Example Usage
-------------

Create session using auto-assigned email address, print email address and print
id of first message in inbox:

    from guerrillamail import GuerrillaMailSession
    session = GuerrillaMailSession()
    print session.get_session_state()['email_address']
    print session.get_email_list()[0].guid


You can now delete an email by:

    session.delete_email(session.get_email_list()[0].guid)

Example CLI Usage
-----------------

Set email address:


    $ guerrillamail setaddr john.doe
    $ guerrillamail info
    Email: john.doe@guerrillamailblock.com


List inbox contents:

    $ guerrillamail list
    (*) 48859781  23:45:27+00:00  spam@example.com
    Example messsage 2

    (*) 48859574  09:25:01+00:00  spam@example.com
    Example message

    ( ) 1         00:00:00+00:00  no-reply@guerrillamail.com
    Welcome to Guerrilla Mail


Read email message:

    $ guerrillamail get 48859781
    From: spam@example.com
    Date: 2016-06-11 23:45:27+00:00
    Subject: Example message 2

    Example Guerrillamail message body.


Using Alternative Guerrillamail Server
--------------------------------------

By default, ``http://api.guerrillamail.com`` is used as the base URL for
Guerrillamail API calls. This can be overridden by providing the ``base_url``
property when constructing a GuerrillaMailSession instance. When using the CLI
the ``base_url`` property can be defined in the ``~/.guerrillamail`` JSON
config file, for example:

    {
        "base_url": "https://api.guerrillamail.com"
    }


License
-------

Python Guerrilla Mail is free software, licensed under the GPLv3.


Guerrillamail: https://www.guerrillamail.com/
