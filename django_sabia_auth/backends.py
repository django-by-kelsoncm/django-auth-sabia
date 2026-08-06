from django.contrib.auth import get_user_model

from .utils import apply_user_attr_map, get_sabia_settings


class SabiaAuthBackend:
    """
    Django authentication backend for Sabiá OAuth2.

    Looks up or creates a Django user based on the profile info returned by Sabiá.

    By default the CPF is used as the Django ``username``. Customize the field
    mapping via ``SABIA_USER_LOOKUP_FIELD`` and ``SABIA_USER_ATTR_MAP`` in your
    Django settings — see the documentation for details.
    """

    def authenticate(self, request, sabia_user_info=None, **kwargs):
        if sabia_user_info is None:
            return None

        cfg = get_sabia_settings()
        lookup_field = cfg["user_lookup_field"]
        attr_map = cfg["user_attr_map"]

        User = get_user_model()
        attrs = apply_user_attr_map(sabia_user_info, attr_map, cfg=cfg)

        lookup_value = attrs.get(lookup_field)
        if not lookup_value:
            return None

        # Separate the lookup key from the remaining defaults.
        defaults = {k: v for k, v in attrs.items() if k != lookup_field}

        user, created = User.objects.get_or_create(
            **{lookup_field: lookup_value},
            defaults=defaults,
        )

        if not created:
            changed = False
            for field, value in defaults.items():
                if getattr(user, field, None) != value:
                    setattr(user, field, value)
                    changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                user.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
