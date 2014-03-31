# -*- coding: utf-8 -*-
import re
from pkg_resources import resource_filename
from string import whitespace

from trac.admin.api import IAdminPanelProvider
from trac.core import Component, implements
from trac.util.translation import dgettext
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import add_notice, add_warning

from api import _
from model import ChangefileBiffConfig

__all__ = ['ChangefileBiffAdminPage']

WHITESPACE_PATTERN = re.compile(u'|'.join(whitespace), re.U)


class ChangefileBiffAdminPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', _('Ticket System'), 'filebiff', _('File Biff'))

    def render_admin_panel(self, req, cat, page, biff_key):
        req.perm.require('TICKET_ADMIN')
        biff_config = ChangefileBiffConfig(self.env, self.config)
        template = 'changefilebiff_admin.html'

        if biff_key:
            # in detail view
            if req.method == 'POST':
                if req.args.get('save') and \
                   self._validate_update(req, biff_key, biff_config):
                    biff_config.update(req.authname, req.args, biff_key)
                    self._add_notice_saved(req)
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            biff = biff_config.biff[biff_key]
            return template, {'view': 'detail', 'biff': biff}

        # in list view
        if req.method == 'POST':

            if req.args.get('add') and self._validate_add(req, biff_config):
                biff_config.add(req.args)
                self._add_notice_saved(req)
                req.redirect(req.href.admin(cat, page))

            elif req.args.get('remove'):
                select_keys = req.args.get('sel')
                if select_keys:
                    if not isinstance(select_keys, list):
                        select_keys = [select_keys]

                    biff_config.remove(req.authname, select_keys)
                    self._add_notice_removed(req)
                    req.redirect(req.href.admin(cat, page))
                else:
                    add_warning(req, _('No Biff configuration selected.'))

        biff_values = biff_config.biff.values()
        return template, {'view': 'list',
                          'biff': biff_config.get_i18n_message_catalog(),
                          'biff_values': biff_values}

    def _validate_add(self, req, biff_config):
        biff_values = biff_config.biff.values()
        return self._validate_common(req, biff_values)

    def _validate_update(self, req, biff_key, biff_config):
        func = lambda x: x['key'] != biff_key
        biff_values = filter(func, biff_config.biff.values())
        return self._validate_common(req, biff_values)

    def _validate_common(self, req, biff_values):
        name = req.args.get('name')
        cc = req.args.get('cc')
        filename = req.args.get('filename')

        if not (name and filename):
            add_warning(req, _('Name and Filename is required.'))
            return False

        if re.search(WHITESPACE_PATTERN, name):
            add_warning(req, _('Whitespace is not allowed for the name.'))
            return False

        if cc:
            all_users = [_u for _u, __, __ in self.env.get_known_users()]
            cc_users = [_u.strip() for _u in cc.split(',')]
            for user in cc_users:
                if user not in all_users:
                    _msg = _("The user '%(user)s' is not existed.", user=user)
                    add_warning(req, _msg)
                    return False

        biff_names = map(lambda x: x['name'], biff_values)
        if name in biff_names:
            add_warning(req, _('The name is already used.'))
            return False

        multiple_fields = ['filename']
        for field_name in multiple_fields:
            if not self._validate_multiple_field(req, field_name, biff_values):
                return False

        return True

    def _validate_multiple_field(self, req, field_name, biff_values):
        _values = map(lambda x: x[field_name], biff_values)
        biff_fvalues = [__f.strip() for _f in _values for __f in _f.split(',')]
        fvalues = [_f.strip() for _f in req.args.get(field_name).split(',')]
        for fvalue in fvalues:
            if fvalue in biff_fvalues:
                _msg = _("The value '%(fvalue)s' is already configured.",
                         fvalue=fvalue)
                add_warning(req, _msg)
                return False
        return True

    def _add_notice_saved(self, req):
        _msg = 'messages'
        add_notice(req, (dgettext)(_msg, 'Your changes have been saved.'))

    def _add_notice_removed(self, req):
        add_notice(req, _("The selected Biff settings have been removed."))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('changefilebiff', resource_filename(__name__, 'htdocs'))]
