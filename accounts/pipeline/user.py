USER_FIELDS = ['email']


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }


def user_details(strategy, details, user=None, *args, **kwargs):
    """Update user profile details using data from provider."""
    if user and user.userprofile:
        changed = False  # flag to track changes
        # TODO: fetch and map all available info from social profile
        allowed = ('first_name', 'last_name', )

        for name, value in details.items():
            if value is not None and hasattr(user.userprofile, name):
                current_value = getattr(user.userprofile, name, None)
                if not current_value or name in allowed:
                    changed |= current_value != value
                    setattr(user.userprofile, name, value)

        social = kwargs.get('social')
        if not user.email and social:
            # XXX: Should be any email to login using JWT
            user.email = social.uid + '@' + social.provider
            user.save()

        if changed:
            user.userprofile.save()
