Python Guerrillamail
====================

Python Guerrillamail is a Python client API and command line interface for
interacting with a `Guerrillamail`_ temporary email server.

.. image:: https://travis-ci.org/ncjones/python-guerrillamail.svg?branch=master
    :target: https://travis-ci.org/ncjones/python-guerrillamail
    :alt: Build Status


Installation
------------

.. code-block:: sh

    pip install python-guerrillamail


Example Usage
-------------

Create session using auto-assigned email address, print email address and print
id of latest message in inbox:

.. code-block:: python

    from guerrillamail import GuerrillaMailSession
    session = GuerrillaMailSession()
    current_email_address = session.get_session_state()['email_address'] #this is the current email address (type string)
    print current_email_address
    
    #get a list of all received emails
    inbox = session.get_email_list()
    
    #each new email is appended to the beginning of the inbox list; 
    #therefore, the latest received email always has position [0]
    latest_received_email = inbox[0] 
    
    #each mail object is identified by its unique guid
    guid = latest_received_email.guid 
    
    #Execute get_email function with guid as argument: this function needs to be called  in order for a mail to be read; 
    #otherwise, the email body will be None.
    email = session.get_email(guid) 
    
    #print every property of the Mail object
    print email.guid, email.sender, email.subject, email.excerpt, email.datetime, email.body, email.read  
    
Create session, keep it running and print every new received email:

.. code-block:: python

    from guerrillamail import GuerrillaMailSession
    from time import sleep
    
    session = GuerrillaMailSession()
    
    read_number = 0 #number of read emails
    read_guids = [] #guids of read emails
    
    while True: #keep the session running
        inbox = session.get_email_list()
        
        if len(inbox) > read_number #check for unread emails:
            for mail_object in inbox:
                if mail_object.guid not in read_guids: #iterate over unread emails
                    full_mail = session.get_email(mail_object.guid) #full Mail object with all properties set
                    print full_mail.sender, full_mail.subject, full_mail.body #print mail 
                    read_guids.append[mail_object.guid] #set mail guid as read
                    read_number +=  1
                    
        sleep(10) #update every 10 seconds
        


    


Example CLI Usage
-----------------

Set email address:

.. code-block::

    $ guerrillamail setaddr john.doe
    $ guerrillamail info
    Email: john.doe@guerrillamailblock.com


List inbox contents:

.. code-block::

    $ guerrillamail list
    (*) 48859781  23:45:27+00:00  spam@example.com
    Example messsage 2

    (*) 48859574  09:25:01+00:00  spam@example.com
    Example message

    ( ) 1         00:00:00+00:00  no-reply@guerrillamail.com
    Welcome to Guerrilla Mail


Read email message:

.. code-block::

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

.. code-block:: json

    {
        "base_url": "https://api.guerrillamail.com"
    }


License
-------

Python Guerrilla Mail is free software, licensed under the GPLv3.


.. _Guerrillamail: https://www.guerrillamail.com/
