About
=====

Python Guerrilla Mail is a Python client API and command line interface for
interacting with a [Guerrillamail](https://www.guerrillamail.com/) temporary
email server.

Python Guerrilla Mail is free software, licensed under the GPLv3.


Usage (Python)
==============

    >>> from guerrillamail import GuerrillaMailSession
    >>> session = GuerrillaMailSession()
    >>> print session.get_session_state()['email_address']
    bzzvxsue@guerrillamailblock.com
    >>> print session.get_email_list()[0].guid
    1
    >>> print session.get_email(1).subject
    Welcome to Guerrilla Mail


Usage (CLI)
===========

    $ python guerrillamail.py setaddr john.doe
    $ python guerrillamail.py info
    Email: john.doe@guerrillamailblock.com
    $ python guerrillamail.py list
    (*) 48859781  09:25:01+00:00  admin@flirt.com
    john3, View all singles who decided to contact you!

    (*) 1         00:00:00+00:00  no-reply@guerrillamail.com
    Welcome to Guerrilla Mail

