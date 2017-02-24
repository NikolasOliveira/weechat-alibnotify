#! /usr/bin/env bash

# VERY Simple script to install the alibnotify plugin in the default weechat location

# Assumptions:
# - weechat installation dir is in the home directory of the user calling this
#   script
# - The caller of this script as the proper privileges to copy the script,
#   make the link, and mkdir in the weechat dir
# - The python script directory exists in the weechat dir (presumably setup if 
#   at least one python weechat script is installed already

cp alibnotify.py ~/.weechat/python
cd ~/.weechat/python/autoload
ln -fs ../alibnotify.py alibnotify.py
