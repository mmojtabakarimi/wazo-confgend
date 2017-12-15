# -*- coding: utf-8 -*-
# Copyright 2016-2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from StringIO import StringIO

from xivo_dao.resources.conference import dao as conference_dao
from xivo_dao.resources.asterisk_file import dao as asterisk_file_dao

from ..helpers.asterisk import AsteriskFileGenerator


class ConfBridgeConfGenerator(object):

    def __init__(self, dependencies):
        self.dependencies = dependencies

    def generate(self):
        asterisk_file_generator = AsteriskFileGenerator(asterisk_file_dao)
        generator = _ConfBridgeConf(conference_dao)
        output = StringIO()
        asterisk_file_generator.generate('confbridge.conf', output)
        generator.generate(output)
        return output.getvalue()


class _ConfBridgeConf(object):

    def __init__(self, dao):
        self.conference_dao = dao

    def generate(self, output):
        conferences = self.conference_dao.find_all_by()
        self._gen_bridge_profile(conferences, output)
        print >> output

        self._gen_user_profile(conferences, output)
        print >> output

        self._gen_default_menu(output)
        print >> output

    def _gen_bridge_profile(self, conferences, output):
        for row in conferences:
            for line in self._format_bridge_profile(row):
                print >> output, line
            print >> output

    def _gen_user_profile(self, conferences, output):
        for row in conferences:
            for line in self._format_user_profile(row):
                print >> output, line
            print >> output

            if row.admin_pin:
                for line in self._format_admin_profile(row):
                    print >> output, line
            print >> output

    def _format_bridge_profile(self, row):
        yield '[xivo-bridge-profile-{}]'.format(row.id)
        yield 'type = bridge'
        yield 'max_members = {}'.format(row.max_users)
        yield 'record_conference = {}'.format(self._convert_bool(row.record))

    def _format_user_profile(self, row):
        yield '[xivo-user-profile-{}]'.format(row.id)
        yield 'type = user'
        yield 'quiet = {}'.format(self._convert_bool(row.quiet_join_leave))
        yield 'announce_join_leave = {}'.format(self._convert_bool(row.announce_join_leave))
        yield 'announce_user_count = {}'.format(self._convert_bool(row.announce_user_count))
        yield 'announce_only_user = {}'.format(self._convert_bool(row.announce_only_user))
        if row.music_on_hold:
            yield 'music_on_hold_when_empty = yes'
            yield 'music_on_hold_class = {}'.format(row.music_on_hold)

    def _format_admin_profile(self, row):
        yield '[xivo-admin-profile-{}](xivo-user-profile-{})'.format(row.id, row.id)
        yield 'admin = yes'

    def _convert_bool(self, option):
        return 'yes' if option else 'no'

    def _gen_default_menu(self, output):
        for line in self._gen_default_user_menu():
            print >> output, line

        print >> output
        for line in self._gen_default_admin_menu():
            print >> output, line

    def _gen_default_user_menu(self):
        yield '[xivo-default-user-menu]'
        yield 'type = menu'
        yield '* = playback_and_continue({})'.format('&'.join(['dir-multi1',
                                                               'digits/1&confbridge-mute-out',
                                                               'digits/4&confbridge-dec-list-vol-out',
                                                               'digits/5&confbridge-rest-list-vol-out',
                                                               'digits/6&confbridge-inc-list-vol-out',
                                                               'digits/7&confbridge-dec-talk-vol-out',
                                                               'digits/8&confbridge-rest-talk-vol-out',
                                                               'digits/9&confbridge-inc-talk-vol-out']))
        yield '1 = toggle_mute'
        yield '4 = decrease_listening_volume'
        yield '5 = reset_listening_volume'
        yield '6 = increase_listening_volume'
        yield '7 = decrease_talking_volume'
        yield '8 = reset_talking_volume'
        yield '9 = increase_talking_volume'

    def _gen_default_admin_menu(self):
        yield '[xivo-default-admin-menu](xivo-default-user-menu)'
        yield '* = playback_and_continue({})'.format('&'.join(['dir-multi1',
                                                               'digits/1&confbridge-mute-out',
                                                               'digits/2&confbridge-lock-out',
                                                               'digits/3&confbridge-remove-last-out',
                                                               'digits/4&confbridge-dec-list-vol-out',
                                                               'digits/5&confbridge-rest-list-vol-out',
                                                               'digits/6&confbridge-inc-list-vol-out',
                                                               'digits/7&confbridge-dec-talk-vol-out',
                                                               'digits/8&confbridge-rest-talk-vol-out',
                                                               'digits/9&confbridge-inc-talk-vol-out']))
        yield '2 = admin_toggle_conference_lock'
        yield '3 = admin_kick_last'
        yield '0 = admin_toggle_mute_participants'
