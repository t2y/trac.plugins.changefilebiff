# -*- coding: utf-8 -*-
from datetime import datetime

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionCache
from trac.ticket import Ticket
from trac.util.datefmt import utc
from trac.util.text import exception_to_unicode
from trac.util.translation import domain_functions
from trac.versioncontrol.api import IRepositoryChangeListener
from tracopt.ticket.commit_updater import CommitTicketUpdater


add_domain, _, N_, gettext, ngettext, tag_ = domain_functions(
    'changefilebiff', ('add_domain', '_', 'N_', 'gettext', 'ngettext', 'tag_'))


from model import ChangefileBiffConfig
from model import FileBiffTicketCustomField


__all__ = ['ChangefileBiffModule', 'ChangefileBiffRepositoryChangeListener']


class ChangefileBiffModule(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        from pkg_resources import resource_exists, resource_filename
        if resource_exists(__name__, 'locale'):
            add_domain(self.env.path, resource_filename(__name__, 'locale'))

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
        pass


class ChangefileBiffRepositoryChangeListener(Component):

    implements(IRepositoryChangeListener)

    def changeset_added(self, repos, changeset):
        biff_names, biff_cc = self._get_biff_names_and_cc(changeset)
        if biff_names:
            self._update_ticket(changeset, biff_names, biff_cc)

    def changeset_modified(self, repos, changeset, old_changeset):
        pass

    def _get_biff_names_and_cc(self, changeset):
        biff_names, biff_cc = set(), set()
        biff_config = ChangefileBiffConfig(self.env, self.config)
        biff_matcher = biff_config.get_filename_matcher()

        for biff in biff_config.biff.values():
            biff_filenames = [_f.strip() for _f in biff['filename'].split(',')]
            match_files = biff_matcher.match_files(
                biff_filenames,
                # chg is (path, kind, change, base_path, base_rev)
                [chg[0] for chg in changeset.get_changes()])

            if any(match_files):
                biff_names.add(biff['name'])
                biff_cc.add(biff['cc'])
        return biff_names, biff_cc

    def _update_ticket(self, changeset, biff_names, biff_cc):
        ticket_updator = self.env.compmgr.components.get(CommitTicketUpdater)
        if not ticket_updator:
            self.env.log.error('CommitTicketUpdater is not available, '
                               'enable it to parse changeset message')
            return

        date = datetime.now(utc)
        tickets = ticket_updator._parse_message(changeset.message)
        perm = PermissionCache(self.env, changeset.author)
        for tkt_id, cmds in tickets.iteritems():
            try:
                has_permission = False
                with self.env.db_transaction:
                    ticket = Ticket(self.env, tkt_id)
                    ticket_perm = perm(ticket.resource)
                    for cmd in cmds:
                        if cmd(ticket, changeset, ticket_perm) is not False:
                            has_permission = True
                    if has_permission:
                        cc_list = ', ' + ', '.join(biff_cc)
                        ticket['cc'] += cc_list
                        fb_field = FileBiffTicketCustomField(ticket)
                        fb_field.add(biff_names)
                        if fb_field.is_updated:
                            ticket.save_changes(changeset.author, '', date)
            except Exception as e:
                self.env.log.error('Unexpected error while processing ticket '
                                   '#%s: %s', tkt_id, exception_to_unicode(e))
