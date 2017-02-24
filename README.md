# alibnotify - A WeeChat Libnotify Script

This is a notification script for [WeeChat](http://weechat.org) Internet Relay Chat client.

Forked from anofity, see [anotify](https://github.com/magnific0/weechat-anotify)

## Features

Notifications for:

- Private message
- Inivtes, topic changes
- Extensive DCC support: chat, file receiving and sending
- Notifications can be made sticky (always or only on away)
- Notifications can be muted/suspended temporarily (see /help alibnotify)
- Noisy public channels can be filtered out, by whitelisting public channels you want to receive notifications from

## Installation

Make sure that Libnotify and Python bindings are installed. Use your favorite package manager

Run the provided `install.sh` script to install the plugin into the users weechat directory

## Settings

### Notification Settings

- `show_public_message`: Notify on public message. (on/off*)
- `public_channel_whitelist`: Allow only these public channels to show notifications ("")
- `show_private_message`: Notify on private message. (on*/off)
- `show_public_action_message`: Notify on public action message. (on/off*)
- `show_private_action_message`: Notify on private action message. (on*/off)
- `show_notice_message`: Notify on notice message. (on/off*)
- `show_invite_message`: Notify on channel invitation message. (on*/off)
- `show_highlighted_message`: Notify on nick highlight. (on*/off)
- `show_server`: Notify on server connect and disconnect. (on*/off)
- `show_channel_topic`: Notify on channel topic change. (on*/off)
- `show_dcc`: Notify on DCC chat/file transfer messages. (on*/off)
- `show_upgrade_ended`: Notify on WeeChat upgrade completion. (on*/off)

### Sticky Settings

- `sticky`: Set sticky notifications. (on/off*)
- `sticky_away`: Set sticky notifications only when away. (on*/off)

