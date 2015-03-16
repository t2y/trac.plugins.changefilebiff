# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import chain
from operator import methodcaller

from trac.ticket import Ticket
from trac.util import hex_entropy
from trac.util.datefmt import utc
from trac.util.text import exception_to_unicode

from api import _
import matcher


class ChangefileBiffConfig(object):
    """Configuration model to handle File Biff settings."""

    SECTION = 'changefilebiff'
    BIFF_KEYS = 'biff_keys'
    BIFF_OPTION = 'biff.%s.%s'  # biff.$key.$field_name
    BIFF_FIELDS = [
        {'id': 'name', 'multiple': False, 'i18n': _('Name')},
        {'id': 'cc', 'multiple': True, 'i18n': _('Cc')},
        {'id': 'filename', 'multiple': True, 'i18n': _('Filename')},
    ]

    def __init__(self, env, config):
        self.env = env
        self.config = config
        self.keys = self.config.getlist(self.SECTION, self.BIFF_KEYS, [])
        self.ticket_custom_config = TicketCustomFileBiffConfig(env, config)
        if not self.ticket_custom_config.has_custom_field():
            self.ticket_custom_config.add_custom_field()

    @property
    def biff(self):
        def get_value(option, is_multiple):
            if is_multiple:
                rv = u', '.join(self.config.getlist(self.SECTION, option, []))
            else:
                rv = self.config.get(self.SECTION, option, '')
            return rv

        biff = {}
        for key in self.keys:
            biff[key] = {'key': key}
            for field in self.BIFF_FIELDS:
                id_ = field['id']
                option = self.BIFF_OPTION % (key, id_)
                biff[key][id_] = get_value(option, field['multiple'])
                biff[key][id_ + '_i18n'] = field['i18n']
        return biff

    @property
    def new_biff_key(self):
        return hex_entropy(16)

    def get_i18n_message_catalog(self):
        catalog = {}
        for field in self.BIFF_FIELDS:
            catalog[field['id'] + '_i18n'] = field['i18n']
        return catalog

    def add(self, opt_value):
        generated_key = self.new_biff_key
        self.set_option(opt_value, generated_key, is_new=True)
        self.ticket_custom_config.add_options_value(opt_value.get('name'))
        self.config.save()
        return generated_key

    def update(self, authname, opt_value, key):
        option = self.BIFF_OPTION % (key, 'name')
        old_value = self.config.get(self.SECTION, option, '')
        self.set_option(opt_value, key)

        new_value = opt_value.get('name')
        self.ticket_custom_config.update_options_value(authname,
                                                       old_value, new_value)
        self.config.save()

    def remove(self, authname, keys):
        old_values = []
        for key in keys:
            option = self.BIFF_OPTION % (key, 'name')
            old_values.append(self.config.get(self.SECTION, option, ''))
            self.remove_option(key)

        self.ticket_custom_config.remove_options_value(authname, old_values)
        self.config.save()

    def set_option(self, opt_value, key, is_new=False):
        if is_new:
            self.keys.append(key)
            self._set_option_biff_keys()

        for field in self.BIFF_FIELDS:
            id_ = field['id']
            value = opt_value.get(id_, u'')
            if field['multiple'] and isinstance(value, (list, tuple)):
                value = u', '.join(value)
            option = self.BIFF_OPTION % (key, id_)
            self.config.set(self.SECTION, option, value)

    def save(self):
        self.config.save()

    def remove_option(self, key):
        try:
            self.keys.pop(self.keys.index(key))
        except ValueError:
            self.env.log.warn('biff key is not found: %s' % key)
        else:
            self._set_option_biff_keys()

        for field in self.BIFF_FIELDS:
            id_ = field['id']
            self.config.remove(self.SECTION, self.BIFF_OPTION % (key, id_))

    def _set_option_biff_keys(self):
        self.config.set(self.SECTION, self.BIFF_KEYS, u', '.join(self.keys))

    def get_filename_matcher(self):
        mp = self.ticket_custom_config.get_matching_pattern_value()
        return matcher.get_filename_matcher(self.env, mp)

class TicketCustomFileBiffConfig(object):
    """Configuration model to handle [ticket-custom] section in trac.ini."""

    SECTION = 'ticket-custom'
    CUSTOM_FIELDS = {
        'id': 'filebiff',
        'type': 'text',
        'properties': [
            ('filebiff.format', 'list'),
            ('filebiff.multiple', 'true'),
            ('filebiff.label', _('Biff')),
            ('filebiff.options', ''),
            ('filebiff.size', '3'),
            ('filebiff.matching_pattern', matcher.DEFAULT_MATCHING_PATTERN),
        ],
    }

    GET_TICKET_ID_FROM_TICKET_CUSTOM = """
        SELECT ticket FROM ticket_custom WHERE name=%s AND value LIKE %s
    """.strip()

    def __init__(self, env, config):
        self.env = env
        self.config = config

    @property
    def fb_options(self):
        return self.CUSTOM_FIELDS['properties'][3][0]

    @property
    def fb_matching_pattern(self):
        return self.CUSTOM_FIELDS['properties'][5][0]

    def has_custom_field(self):
        return self.CUSTOM_FIELDS['id'] in self.config['ticket-custom']

    def add_custom_field(self):
        ticket_custom = self.config['ticket-custom']
        field = self.CUSTOM_FIELDS
        ticket_custom.set(field['id'], field['type'])
        for key, value in field['properties']:
            ticket_custom.set(key, value)
        self.config.save()
        _msg = '%s [%s] settings into [ticket-custom] is added in trac.ini'
        self.env.log.info(_msg % (field['id'], field['type']))

    def get_options_value(self):
        current_values = self.config.get(self.SECTION, self.fb_options, '')
        return set(current_values.split())

    def add_options_value(self, value):
        values = self.get_options_value()
        if value not in values:
            values.add(value)
            self.set_fb_options(values)

    def update_options_value(self, authname, old_value, new_value):
        values = self.get_options_value()
        if old_value in values:
            values.discard(old_value)
            values.add(new_value)
            self.set_fb_options(values)
            self.update_ticket_field(authname, old_value, new_value)

    def update_ticket_field(self, authname, old_value, new_value):
        ticket_ids = self._get_ticket_ids(old_value)
        if not ticket_ids:
            return

        comment = _('Updated File Biff field value by Trac administrator.')
        fb_methodcaller = methodcaller('update', old_value, new_value)
        self._update_field(authname, comment, ticket_ids, fb_methodcaller)

    def remove_options_value(self, authname, remove_values):
        values = self.get_options_value()
        has_remove_value = False
        for value in remove_values:
            if value in values:
                values.remove(value)
                has_remove_value = True

        if has_remove_value:
            self.set_fb_options(values)
            self.remove_ticket_field(authname, remove_values)

    def remove_ticket_field(self, authname, remove_values):
        for value in remove_values:
            ticket_ids = self._get_ticket_ids(value)
            if not ticket_ids:
                continue

            comment = _('Removed File Biff field value by Trac administrator.')
            fb_methodcaller = methodcaller('remove', value)
            self._update_field(authname, comment, ticket_ids, fb_methodcaller)

    def set_fb_options(self, values):
        updated_values = u' '.join(sorted(list(values)))
        self.config.set(self.SECTION, self.fb_options, updated_values)

    def save(self):
        self.config.save()

    def _get_ticket_ids(self, value):
        ticket_ids = []
        sql = self.GET_TICKET_ID_FROM_TICKET_CUSTOM
        params = (self.CUSTOM_FIELDS['id'], '%%%s%%' % value)
        try:
            with self.env.db_query as db:
                ticket_ids = [id_ for id_ in db(sql, params)]
        except Exception as e:
            self.env.log.error('Failed to get ticket ids: '
                               'sql: %s, params: %s, exception: %s',
                               sql, params, exception_to_unicode(e))
        return ticket_ids

    def _update_field(self, authname, comment, ticket_ids, fb_methodcaller):
        date = datetime.now(utc)
        for tkt_id in chain.from_iterable(ticket_ids):
            try:
                with self.env.db_transaction:
                    ticket = Ticket(self.env, tkt_id)
                    fb_field = FileBiffTicketCustomField(ticket)
                    fb_methodcaller(fb_field)
                    if fb_field.is_updated:
                        ticket.save_changes(authname, comment, date)
            except Exception as e:
                self.env.log.error(
                    'Failed to update ticket file biff field value: '
                    'tkt id: %s, authname: %s, exception: %s',
                    tkt_id, authname, exception_to_unicode(e))

    def get_matching_pattern_value(self):
        return self.config.get(self.SECTION, self.fb_matching_pattern, '')


class FileBiffTicketCustomField(object):
    """File Biff field model to handle the ticket custom field."""

    field_name = TicketCustomFileBiffConfig.CUSTOM_FIELDS['id']

    def __init__(self, ticket):
        self.ticket = ticket
        self.is_updated = False

    def get_values(self):
        value = self.ticket.get_value_or_default(self.field_name)
        return value.split() if value else []

    def add(self, add_values):
        values = self.get_values()
        for value in add_values:
            if value not in values:
                values.append(value)
                self.is_updated = True

        if self.is_updated:
            values.sort()
            self.ticket[self.field_name] = u' '.join(values)

    def update(self, old_value, new_value):
        values = self.get_values()
        if old_value in values:
            values.pop(values.index(old_value))
            values.append(new_value)
            values.sort()
            self.ticket[self.field_name] = u' '.join(values)
            self.is_updated = True

    def remove(self, remove_value):
        values = self.get_values()
        if remove_value in values:
            values.pop(values.index(remove_value))
            self.ticket[self.field_name] = u' '.join(values)
            self.is_updated = True

    def save_values(self, author, comment=''):
        self.ticket.save_changes(author, comment, datetime.now(utc))
