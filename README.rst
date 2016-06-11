Python Guerrillamail
====================

Python Guerrillamail is a Python client API and command line interface for
interacting with a `Guerrillamail`_ temporary email server.

.. image:: https://travis-ci.org/ncjones/python-guerrillamail.svg?branch=master
    :target: https://travis-ci.org/ncjones/python-guerrillamail
    :alt: Build Status


Usage (Python)
--------------

.. code-block:: python

    from guerrillamail import GuerrillaMailSession
    session = GuerrillaMailSession()
    print session.get_session_state()['email_address']
    print session.get_email_list()[0].guid


Usage (CLI)
-----------

.. code-block::

    $ python guerrillamail.py setaddr john.doe
    $ python guerrillamail.py info
    Email: john.doe@guerrillamailblock.com
    $ python guerrillamail.py list
    (*) 48859781  09:25:01+00:00  admin@flirt.com
    john3, View all singles who decided to contact you!

    (*) 1         00:00:00+00:00  no-reply@guerrillamail.com
    Welcome to Guerrilla Mail


Using Alternative Guerrillamail Server
--------------------------------------

By default, ``http://api.guerrillamail.com`` is used as the base URL for
Guerrillamail API calls. This can be overridden by providing the ``base_url``
property when constructing a GuerrillaMailSession instance. When using the CLI
the ``base_url`` property can be defined in the ``~/.guerrillamail`` JSON
config file, for example:

.. code-block:: json

    {
        "base_url": "https://api.guerrillamail.com"
    }


License
-------

Python Guerrilla Mail is free software, licensed under the GPLv3.


.. _Guerrillamail: https://www.guerrillamail.com/
