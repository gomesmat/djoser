from copy import deepcopy

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils import six
from django.utils.functional import LazyObject, empty
from django.test.signals import setting_changed


DJOSER_SETTINGS_NAMESPACE = 'DJOSER'


default_settings = {
    'USE_HTML_EMAIL_TEMPLATES': False,
    'SEND_ACTIVATION_EMAIL': False,
    'SEND_CONFIRMATION_EMAIL': False,
    'SET_PASSWORD_RETYPE': False,
    'SET_USERNAME_RETYPE': False,
    'PASSWORD_RESET_CONFIRM_RETYPE': False,
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': False,
    'ROOT_VIEW_URLS_MAPPING': {},
    'PASSWORD_VALIDATORS': [],
    'SERIALIZERS': {
        'activation': 'djoser.serializers.ActivationSerializer',
        'login': 'djoser.serializers.LoginSerializer',
        'password_reset': 'djoser.serializers.PasswordResetSerializer',
        'password_reset_confirm': 'djoser.serializers.PasswordResetConfirmSerializer',
        'password_reset_confirm_retype': 'djoser.serializers.PasswordResetConfirmRetypeSerializer',
        'set_password': 'djoser.serializers.SetPasswordSerializer',
        'set_password_retype': 'djoser.serializers.SetPasswordRetypeSerializer',
        'set_username': 'djoser.serializers.SetUsernameSerializer',
        'set_username_retype': 'djoser.serializers.SetUsernameRetypeSerializer',
        'user_registration': 'djoser.serializers.UserRegistrationSerializer',
        'user': 'djoser.serializers.UserSerializer',
        'token': 'djoser.serializers.TokenSerializer',
    },
    'LOGOUT_ON_PASSWORD_CHANGE': False,
}


def get(key):
    user_settings = merge_settings_dicts(
        deepcopy(default_settings), getattr(settings, DJOSER_SETTINGS_NAMESPACE, {}))
    try:
        return user_settings[key]
    except KeyError:
        raise ImproperlyConfigured('Missing settings: {}[\'{}\']'.format(DJOSER_SETTINGS_NAMESPACE, key))


def merge_settings_dicts(a, b, path=None, overwrite_conflicts=True):
    """merges b into a, modify a in place

    Found at http://stackoverflow.com/a/7205107/1472229
    """
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_settings_dicts(a[key], b[key], path + [str(key)], overwrite_conflicts=overwrite_conflicts)
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                if overwrite_conflicts:
                    a[key] = b[key]
                else:
                    conflict_path = '.'.join(path + [str(key)])
                    raise Exception('Conflict at %s' % conflict_path)
        else:
            a[key] = b[key]
    # Don't let this fool you that a is not modified in place
    return a


class Settings(object):
    def __init__(self, default_settings, explicit_overriden_settings=None):
        if explicit_overriden_settings is None:
            explicit_overriden_settings = {}

        for setting_name, setting_value in six.iteritems(default_settings):
            if setting_name.isupper():
                setattr(self, setting_name, setting_value)

        overriden_djoser_settings = getattr(settings, DJOSER_SETTINGS_NAMESPACE, {}) or explicit_overriden_settings
        for overriden_setting_name, overriden_setting_value in six.iteritems(overriden_djoser_settings):
            value = overriden_setting_value
            if isinstance(overriden_setting_value, dict):
                value = getattr(self, overriden_setting_name, {})
                value.update(overriden_setting_value)
            setattr(self, overriden_setting_name, value)


class LazySettings(LazyObject):
    def _setup(self, explicit_overriden_settings=None):
        self._wrapped = Settings(default_settings, explicit_overriden_settings)

    def __getattr__(self, name):
        """
        Return the value of a setting and cache it in self.__dict__.
        """
        if self._wrapped is empty:
            self._setup()
        val = getattr(self._wrapped, name)
        # self.__dict__[name] = val
        return val


config = Settings(default_settings)


def reload_djoser_settings(*args, **kwargs):
    import ipdb
    ipdb.set_trace()
    global config
    setting, value = kwargs['setting'], kwargs['value']
    if setting == DJOSER_SETTINGS_NAMESPACE:
        config = Settings(default_settings, explicit_overriden_settings=value)
        # config._setup(explicit_overriden_settings=value)


setting_changed.connect(reload_djoser_settings)

