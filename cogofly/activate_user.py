from social_core.exceptions import AuthException
from cogofly.models import User

def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current auth with a user with the same email address in the DB.

    This pipeline entry is not 100% secure unless you know that the providers
    enabled enforce email verification on their side, otherwise a user can
    attempt to take over another user account by using the same (not validated)
    email address on some provider.  This pipeline entry is disabled by
    default.
    """    
    if user:
        user.is_active = True
        user.save()
        return None

    if email := details.get('email'):
        # Try to associate accounts registered with the same email address,
        # only if it's a single object. AuthException is raised if multiple
        # objects are returned.
        users = list(User._base_manager.filter(email=email))
        if not users:
            return None
        elif len(users) > 1:
            raise AuthException(
                backend,
                'The given email address is associated with another account'
            )
        else:
            user = users[0]
            user.is_active = True
            user.save()
            return {'user': user,
                    'is_new': False}