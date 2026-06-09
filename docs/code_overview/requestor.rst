###########
 Requestor
###########

The :class:`.Requestor` is the lowest-level component in prawcore. It wraps a
:class:`requests.Session` and is responsible for issuing the actual HTTP requests to
Reddit. Subclass it to customize request behavior, for example to add caching or
logging.

.. autoclass:: prawcore.requestor.Requestor
    :inherited-members:
