################
 Authentication
################

prawcore separates authentication into two responsibilities:

- **Authenticators** identify your registered Reddit application.
- **Authorizers** use an authenticator to obtain and refresh the OAuth2 access tokens
  that authorize individual requests.

****************
 Authenticators
****************

.. autoclass:: prawcore.auth.BaseAuthenticator
    :inherited-members:

.. autoclass:: prawcore.auth.TrustedAuthenticator
    :inherited-members:

.. autoclass:: prawcore.auth.UntrustedAuthenticator
    :inherited-members:

*************
 Authorizers
*************

.. autoclass:: prawcore.auth.BaseAuthorizer
    :inherited-members:

.. autoclass:: prawcore.auth.Authorizer
    :inherited-members:

.. autoclass:: prawcore.auth.DeviceIDAuthorizer
    :inherited-members:

.. autoclass:: prawcore.auth.ImplicitAuthorizer
    :inherited-members:

.. autoclass:: prawcore.auth.ReadOnlyAuthorizer
    :inherited-members:

.. autoclass:: prawcore.auth.ScriptAuthorizer
    :inherited-members:
