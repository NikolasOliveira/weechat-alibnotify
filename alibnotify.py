# -*- coding: utf-8 -*-
#
# alibnotify.py
# Copyright NikolasOliveira
#
# Forked from
#   anotify.py
#   Copyright (c) 2012 magnific0
#     based on:
#     growl.py
#     Copyright (c) 2011 Sorin Ionescu <sorin.ionescu@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


SCRIPT_NAME = 'alibnotify'
SCRIPT_AUTHOR = 'NikolasOliveira'
SCRIPT_VERSION = '1.3.0'
SCRIPT_LICENSE = 'MIT'
SCRIPT_DESC = 'Sends libnotify notifications upon events.'


# Changelog
# 2017-03-16: v1.3.0 Add alibnotify bar item. It shows mute state if
#                    muted, so the user doesn't forget that their
#                    notificaitions are muted. It will also display the minutes
#                    remaining for a timed mute. The bar item is: alibnotify
# 2017-02-24: v1.2.0 Add /alibnotify command. First arg "mute" allows the user
#                    to disable/mute notifications (either by toggle or
#                    providing a time for how long notifications should be
#                    disabled)
# 2017-02-23: v1.1.0 Add whitelist functionality. This allows users to opt in
#                    to receiving public channel notifications but filter down
#                    to only the channels they're interested. Filtering out
#                    noisy channels that contain bot/automated messages.
#                    The whitelist is a string of channel short names, E.g.:
#                       "#channelicareabout,#anotherchannelilike"
# 2017-02-23: v1.0.2 Add install script
# 2017-02-23: v1.0.1 Fork from anotify
# 2012-09-20: v1.0.0 Forked from original and adapted for libnotify.

# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------
SETTINGS = {
    'show_public_message': 'off',
    'show_private_message': 'on',
    'show_public_action_message': 'off',
    'show_private_action_message': 'on',
    'show_notice_message': 'off',
    'show_invite_message': 'on',
    'show_highlighted_message': 'on',
    'show_server': 'on',
    'show_channel_topic': 'on',
    'show_dcc': 'on',
    'show_upgrade_ended': 'on',
    'public_channel_whitelist': "",
    'sticky': 'off',
    'sticky_away': 'on',
    'icon': '/usr/share/pixmaps/weechat.xpm',
}


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
try:
    import re
    import weechat
    import pynotify
    IMPORT_OK = True
except ImportError as error:
    IMPORT_OK = False
    if str(error).find('weechat') != -1:
        print('This script must be run under WeeChat.')
        print('Get WeeChat at http://www.weechat.org.')
    else:
        weechat.prnt('', 'alibnotify: {0}'.format(error))

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
TAGGED_MESSAGES = {
    'public message or action': set(['irc_privmsg', 'notify_message']),
    'private message or action': set(['irc_privmsg', 'notify_private']),
    'notice message': set(['irc_notice', 'notify_private']),
    'invite message': set(['irc_invite', 'notify_highlight']),
    'channel topic': set(['irc_topic', ]),
    #'away status': set(['away_info', ]),
}


UNTAGGED_MESSAGES = {
    'away status':
        re.compile(r'^You ((\w+).){2,3}marked as being away', re.UNICODE),
    'dcc chat request':
        re.compile(r'^xfer: incoming chat request from (\w+)', re.UNICODE),
    'dcc chat closed':
        re.compile(r'^xfer: chat closed with (\w+)', re.UNICODE),
    'dcc get request':
        re.compile(
            r'^xfer: incoming file from (\w+) [^:]+: ((?:,\w|[^,])+),',
            re.UNICODE),
    'dcc get completed':
        re.compile(r'^xfer: file ([^\s]+) received from \w+: OK', re.UNICODE),
    'dcc get failed':
        re.compile(
            r'^xfer: file ([^\s]+) received from \w+: FAILED',
            re.UNICODE),
    'dcc send completed':
        re.compile(r'^xfer: file ([^\s]+) sent to \w+: OK', re.UNICODE),
    'dcc send failed':
        re.compile(r'^xfer: file ([^\s]+) sent to \w+: FAILED', re.UNICODE),
}


DISPATCH_TABLE = {
    'away status': 'set_away_status',
    'public message or action': 'notify_public_message_or_action',
    'private message or action': 'notify_private_message_or_action',
    'notice message': 'notify_notice_message',
    'invite message': 'notify_invite_message',
    'channel topic': 'notify_channel_topic',
    'dcc chat request': 'notify_dcc_chat_request',
    'dcc chat closed': 'notify_dcc_chat_closed',
    'dcc get request': 'notify_dcc_get_request',
    'dcc get completed': 'notify_dcc_get_completed',
    'dcc get failed': 'notify_dcc_get_failed',
    'dcc send completed': 'notify_dcc_send_completed',
    'dcc send failed': 'notify_dcc_send_failed',
}


STATE = {
    'icon': None,
    'is_away': False,
    'is_muted': False
}


# -----------------------------------------------------------------------------
# Notifiers
# -----------------------------------------------------------------------------
def cb_irc_server_connected(data, signal, signal_data):
    '''Notify when connected to IRC server.'''
    if weechat.config_get_plugin('show_server') == 'on':
        a_notify(
            'Server',
            'Server Connected',
            'Connected to network {0}.'.format(signal_data))
    return weechat.WEECHAT_RC_OK


def cb_irc_server_disconnected(data, signal, signal_data):
    '''Notify when disconnected to IRC server.'''
    if weechat.config_get_plugin('show_server') == 'on':
        a_notify(
            'Server',
            'Server Disconnected',
            'Disconnected from network {0}.'.format(signal_data))
    return weechat.WEECHAT_RC_OK


def cb_notify_upgrade_ended(data, signal, signal_data):
    '''Notify on end of WeeChat upgrade.'''
    if weechat.config_get_plugin('show_upgrade_ended') == 'on':
        a_notify(
            'WeeChat',
            'WeeChat Upgraded',
            'WeeChat has been upgraded.')
    return weechat.WEECHAT_RC_OK


def notify_highlighted_message(prefix, message):
    '''Notify on highlighted message.'''
    if weechat.config_get_plugin("show_highlighted_message") == "on":
        a_notify(
            'Highlight',
            'Highlighted Message',
            "{0}: {1}".format(prefix, message),
            priority=pynotify.URGENCY_CRITICAL)


def notify_public_message_or_action(prefix, message, highlighted, buffer_short_name):
    '''Notify on public message or action.'''
    if prefix == ' *':
        regex = re.compile(r'^(\w+) (.+)$', re.UNICODE)
        match = regex.match(message)
        if match:
            prefix = match.group(1)
            message = match.group(2)
            notify_public_action_message(prefix, message, highlighted, buffer_short_name)
    else:
        if highlighted:
            notify_highlighted_message(prefix, message)
        elif weechat.config_get_plugin("show_public_message") == "on":
            # filter through channel whitelist
            white_list = weechat.config_get_plugin("public_channel_whitelist")
            if not white_list:
                a_notify(
                    'Public',
                    'Public Message in %s' % buffer_short_name,
                    '{0}: {1}'.format(prefix, message))
            elif buffer_short_name in white_list:
                a_notify(
                    'Public',
                    'Public Message in %s' % buffer_short_name,
                    '{0}: {1}'.format(prefix, message))



def notify_private_message_or_action(prefix, message, highlighted, buffer_short_name):
    '''Notify on private message or action.'''
    regex = re.compile(r'^CTCP_MESSAGE.+?ACTION (.+)$', re.UNICODE)
    match = regex.match(message)
    if match:
        notify_private_action_message(prefix, match.group(1), highlighted)
    else:
        if prefix == ' *':
            regex = re.compile(r'^(\w+) (.+)$', re.UNICODE)
            match = regex.match(message)
            if match:
                prefix = match.group(1)
                message = match.group(2)
                notify_private_action_message(prefix, message, highlighted, buffer_short_name)
        else:
            if highlighted:
                notify_highlighted_message(prefix, message)
            elif weechat.config_get_plugin("show_private_message") == "on":
                a_notify(
                    'Private',
                    'Private Message - %s' % prefix,
                    message)


def notify_public_action_message(prefix, message, highlighted, buffer_short_name):
    '''Notify on public action message.'''
    if highlighted:
        notify_highlighted_message(prefix, message)
    elif weechat.config_get_plugin("show_public_action_message") == "on":
        a_notify(
            'Action',
            'Public Action Message',
            '{0}: {1}'.format(prefix, message),
            priority=pynotify.URGENCY_NORMAL)


def notify_private_action_message(prefix, message, highlighted, buffer_short_name):
    '''Notify on private action message.'''
    if highlighted:
        notify_highlighted_message(prefix, message)
    elif weechat.config_get_plugin("show_private_action_message") == "on":
        a_notify(
            'Action',
            'Private Action Message',
            '{0}: {1}'.format(prefix, message),
            priority=pynotify.URGENCY_NORMAL)


def notify_notice_message(prefix, message, highlighted, buffer_short_name):
    '''Notify on notice message.'''
    regex = re.compile(r'^([^\s]*) [^:]*: (.+)$', re.UNICODE)
    match = regex.match(message)
    if match:
        prefix = match.group(1)
        message = match.group(2)
        if highlighted:
            notify_highlighted_message(prefix, message)
        elif weechat.config_get_plugin("show_notice_message") == "on":
            a_notify(
                'Notice',
                'Notice Message',
                '{0}: {1}'.format(prefix, message))


def notify_invite_message(prefix, message, highlighted, buffer_short_name):
    '''Notify on channel invitation message.'''
    if weechat.config_get_plugin("show_invite_message") == "on":
        regex = re.compile(
            r'^You have been invited to ([^\s]+) by ([^\s]+)$', re.UNICODE)
        match = regex.match(message)
        if match:
            channel = match.group(1)
            nick = match.group(2)
            a_notify(
                'Invite',
                'Channel Invitation',
                '{0} has invited you to join {1}.'.format(nick, channel))


def notify_channel_topic(prefix, message, highlighted, buffer_short_name):
    '''Notify on channel topic change.'''
    if weechat.config_get_plugin("show_channel_topic") == "on":
        regex = re.compile(
            r'^\w+ has (?:changed|unset) topic for ([^\s]+)' +
                '(?:(?: from "(?:(?:"\w|[^"])+)")? to "((?:"\w|[^"])+)")?',
            re.UNICODE)
        match = regex.match(message)
        if match:
            channel = match.group(1)
            topic = match.group(2) or ''
            a_notify(
                'Channel',
                'Channel Topic',
                "{0}: {1}".format(channel, topic))


def notify_dcc_chat_request(match):
    '''Notify on DCC chat request.'''
    if weechat.config_get_plugin("show_dcc") == "on":
        nick = match.group(1)
        a_notify(
            'DCC',
            'Direct Chat Request',
            '{0} wants to chat directly.'.format(nick))


def notify_dcc_chat_closed(match):
    '''Notify on DCC chat termination.'''
    if weechat.config_get_plugin("show_dcc") == "on":
        nick = match.group(1)
        a_notify(
            'DCC',
            'Direct Chat Ended',
            'Direct chat with {0} has ended.'.format(nick))


def notify_dcc_get_request(match):
    'Notify on DCC get request.'
    if weechat.config_get_plugin("show_dcc") == "on":
        nick = match.group(1)
        file_name = match.group(2)
        a_notify(
            'DCC',
            'File Transfer Request',
            '{0} wants to send you {1}.'.format(nick, file_name))


def notify_dcc_get_completed(match):
    'Notify on DCC get completion.'
    if weechat.config_get_plugin("show_dcc") == "on":
        file_name = match.group(1)
        a_notify('DCC', 'Download Complete', file_name)


def notify_dcc_get_failed(match):
    'Notify on DCC get failure.'
    if weechat.config_get_plugin("show_dcc") == "on":
        file_name = match.group(1)
        a_notify('DCC', 'Download Failed', file_name)


def notify_dcc_send_completed(match):
    'Notify on DCC send completion.'
    if weechat.config_get_plugin("show_dcc") == "on":
        file_name = match.group(1)
        a_notify('DCC', 'Upload Complete', file_name)


def notify_dcc_send_failed(match):
    'Notify on DCC send failure.'
    if weechat.config_get_plugin("show_dcc") == "on":
        file_name = match.group(1)
        a_notify('DCC', 'Upload Failed', file_name)


# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------
def set_away_status(match):
    status = match.group(1)
    if status == 'been ':
        STATE['is_away'] = True
    if status == 'longer ':
        STATE['is_away'] = False


def cb_process_message(
    data,
    wbuffer,
    date,
    tags,
    displayed,
    highlight,
    prefix,
    message
):
    '''Delegates incoming messages to appropriate handlers.'''
    tags = set(tags.split(','))
    functions = globals()
    is_public_message = tags.issuperset(
        TAGGED_MESSAGES['public message or action'])
    buffer_name = weechat.buffer_get_string(wbuffer, 'name')
    buffer_short_name = weechat.buffer_get_string(wbuffer, 'short_name')
    dcc_buffer_regex = re.compile(r'^irc_dcc\.', re.UNICODE)
    dcc_buffer_match = dcc_buffer_regex.match(buffer_name)
    highlighted = False
    if int(highlight):
        highlighted = True
    # Private DCC message identifies itself as public.
    if is_public_message and dcc_buffer_match:
        notify_private_message_or_action(prefix, message, highlighted, buffer_short_name)
        return weechat.WEECHAT_RC_OK
    # Pass identified, untagged message to its designated function.
    for key, value in UNTAGGED_MESSAGES.items():
        match = value.match(message)
        if match:
            functions[DISPATCH_TABLE[key]](match)
            return weechat.WEECHAT_RC_OK
    # Pass identified, tagged message to its designated function.
    for key, value in TAGGED_MESSAGES.items():
        if tags.issuperset(value):
            functions[DISPATCH_TABLE[key]](prefix, message, highlighted, buffer_short_name)
            return weechat.WEECHAT_RC_OK
    return weechat.WEECHAT_RC_OK


def a_notify(notification, title, description, priority=pynotify.URGENCY_LOW):
    '''Assemble and show the notification'''
    is_away = STATE['is_away']
    if STATE['is_muted']:
        weechat.prnt('', 'alibnotify is currently muted, '
                     'not showing notification. Unmute with: /alibnotify mute')
        return
    icon = STATE['icon']
    time_out = 5000
    if weechat.config_get_plugin('sticky') == 'on':
        time_out = 0
    if weechat.config_get_plugin('sticky_away') == 'on' and is_away:
        time_out = 0
    try:
        pynotify.init("wee-notifier")
        wn = pynotify.Notification(title, description, icon)
        wn.set_urgency(priority)
        wn.set_timeout(time_out)
        wn.show()
    except Exception as error:
        weechat.prnt('', 'alibnotify: {0}'.format(error))


def schedule_decrement(poll_time_m):
    """Schedule the mute time to be decremented in <poll_time_m> minutes"""
    weechat.hook_timer(poll_time_m * 1000 * 60, 0, 1, 'decrement_mute_time_cb',
                       str(poll_time_m))


def mute(arg_list):
    """Depending on the args passed from the user, either toggle the mute state
    Or set mute to True for N minutes"""
    # Unhook any previous timers, because we are either unmuting, muting
    # indefinitely or setting a new timer
    prev_timer_hook = STATE.get('mute_timer')
    if prev_timer_hook:
        weechat.unhook(prev_timer_hook)
        weechat.prnt('', 'unhooking previous mute timer, since this is a new '
                     'mute')
        # If we had a previous timer, also zero out the countdown time
        STATE['mute_time'] = 0

    if len(arg_list) == 1:
        # Just toggle the mute state
        STATE['is_muted'] = not STATE['is_muted']
    elif len(arg_list) == 2:
        # A second arg, the time to remain muted, was provided
        time_to_mute = int(arg_list[1])

        STATE['is_muted'] = True

        # Store the mute time to be displayed in the status bar item, also
        # decrement it periodically so the bar item displays a countdown until
        # notifications will be unmuted
        STATE['mute_time'] = time_to_mute
        schedule_decrement(1)

        # Schedule alibnotify to be unmuted after we've hit the requested time
        timer_hook = weechat.hook_timer(time_to_mute * 1000 * 60, 0, 1,
                                        'unmute_cb', str(time_to_mute))
        STATE['mute_timer'] = timer_hook

    # update bar item to show the current mute state
    weechat.bar_item_update(SCRIPT_NAME)


# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------
def alibnotify_cb(data, buffer, args):
    """Callback for alibnotify command. Current ability includes toggle message
    muting with /alibnotify mute <timer>"""
    arg_list = args.split()
    if 'mute' in args:
        mute(arg_list)
    else:
        weechat.prnt(buffer, 'Unrecognized arg to /alibnotify!')
        weechat.command(buffer, '/help alibnotify')
        return weechat.WEECHAT_RC_ERROR

    return weechat.WEECHAT_RC_OK


def bar_item_build_cb(data, item, window):
    """Update the alibnotify bar item to reflect current state"""
    if STATE['is_muted']:
        bar_text = 'notifications: muted'
        if 'mute_time' in STATE and STATE['mute_time'] > 0:
            bar_text += ' (%dm)' % STATE['mute_time']
        # Colour the text red
        bar_text = weechat.string_eval_expression('${color:red}%s' % bar_text,
                                                  {}, {}, {})
        return bar_text
    else:
        return ''


def decrement_mute_time_cb(data, remaing_calls):
    """Reduce mute time state, to create a countdown of sorts. This state is
    displayed in the alibnotify bar item"""
    STATE['mute_time'] = STATE['mute_time'] - int(data)

    # update bar item to show the current mute state
    weechat.bar_item_update(SCRIPT_NAME)

    # Check if we should schedule another decrements
    if STATE['mute_time'] > 0:
        schedule_decrement(int(data))

    return weechat.WEECHAT_RC_OK


def unmute_cb(data, remaing_calls):
    """Unset the is_muted state"""
    STATE['is_muted'] = False
    weechat.prnt('', 'Unmuting after %sm timer' % data)

    # update bar item to show that we're unmuted
    weechat.bar_item_update(SCRIPT_NAME)

    return weechat.WEECHAT_RC_OK


ALIBNOTIFY_COMMAND_HELP = """
Suspend alibnotify notifications for N minutes with:
    /alibnotify mute <N minutes to stay muted>

Toggle notification with:
    /alibnotify mute

"""

ALIBNOTIFY_COMMAND_COMPLETION = 'mute'


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    '''Sets up WeeChat notifications.'''
    # Initialize options.
    for option, value in SETTINGS.items():
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, value)
    # Initialize.
    icon = "/usr/share/pixmaps/weechat.xpm"
    STATE['icon'] = icon
    # Register hooks.
    weechat.hook_signal(
        'irc_server_connected',
        'cb_irc_server_connected',
        '')
    weechat.hook_signal(
        'irc_server_disconnected',
        'cb_irc_server_disconnected',
        '')
    weechat.hook_signal('upgrade_ended', 'cb_upgrade_ended', '')
    weechat.hook_print('', '', '', 1, 'cb_process_message', '')
    weechat.hook_command('alibnotify', ALIBNOTIFY_COMMAND_HELP,
                         '', '', ALIBNOTIFY_COMMAND_COMPLETION,
                         'alibnotify_cb', '')
    # Create bar item
    alibnotify_bar_item = weechat.bar_item_new(SCRIPT_NAME,
                                               'bar_item_build_cb', '')
    weechat.prnt('', 'alibnotify bar item: %s' % alibnotify_bar_item)
    STATE['bar_item'] = alibnotify_bar_item


if __name__ == '__main__' and IMPORT_OK and weechat.register(
    SCRIPT_NAME,
    SCRIPT_AUTHOR,
    SCRIPT_VERSION,
    SCRIPT_LICENSE,
    SCRIPT_DESC,
    '',
    ''
):
    main()
