##########
 Sessions
##########

A :class:`.Session` ties an authorizer to a requestor and exposes the
:meth:`.Session.request` method that PRAW uses to communicate with Reddit. The
:func:`.session` helper is the recommended way to construct one.

.. autofunction:: prawcore.sessions.session

.. autoclass:: prawcore.sessions.Session
    :inherited-members:
