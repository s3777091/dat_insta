#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from function.dat_insta import dat_insta
import argparse
from function import printcolors as pc
import sys
import signal

is_windows = False

try:
    import gnureadline
except:
    is_windows = True
    import pyreadline


def cmdlist():
    pc.printout("location\t\t")
    print("tìm tất cả địa chỉ trên các bức ảnh nó checking")
    pc.printout("flusremail\t")
    print("lấy địa chỉ email của mấy đứa nó follow")
    pc.printout("flemail\t")
    print("lấy địa chỉ email của mấy đứa nó follow")
    pc.printout("fluserphone\t")
    print("tìm số đth của mấy đứa nó follow")
    pc.printout("flphone\t")
    print("tìm số đth của mấy đứa nó follow")
    pc.printout("info\t\t")
    print("Get target info")
    pc.printout("photouser\t\t")
    print("tải mấy ảnh của nó")
    pc.printout("photoprofile\t\t")
    print("lấy ảnh avatar")
    pc.printout("media\t\t")
    print("tải media của nó")
    pc.printout("stories\t\t")
    print("tải mấy ảnh stories")
    pc.printout("target\t\t")
    print("chọn đứa khác")


def signal_handler(sig, frame):
    pc.printout("\nđi đây!\n", pc.RED)
    sys.exit(0)


def completer(text, state):
    options = [i for i in commands if i.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None


def _quit():
    pc.printout("tôi đi đây!\n", pc.RED)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if is_windows:
    pyreadline.Readline().parse_and_bind("tab: complete")
    pyreadline.Readline().set_completer(completer)
else:
    gnureadline.parse_and_bind("tab: complete")
    gnureadline.set_completer(completer)

parser = argparse.ArgumentParser(description='cái này không phải hack insta mà là tìm thông tin trên insta lập trình bởi đạt huỳnh'
                                             'mục để để tìm kiếm thông tin ẩn của insta mà người dùng không biết')
parser.add_argument('id', type=str,  # var = id
                    help='username')
parser.add_argument('-j', '--json', help='save commands output as JSON file', action='store_true')
parser.add_argument('-f', '--file', help='save output in a file', action='store_true')

args = parser.parse_args()

api = dat_insta(args.id, args.file, args.json)

commands = {
    'list': cmdlist,
    'help': cmdlist,
    'quit': _quit,
    'exit': _quit,
    'location': api.get_location,
    'fluseremail': api.get_fluseremail,
    'flemail': api.get_flemail,
    'fluserphone': api.get_flphone,
    'flphone': api.get_flphone,
    'info': api.get_user_info,
    'photouser': api.get_user_photo,
    'media': api.get_media_type,
    'photoprofile': api.get_user_profile_picture,
    'stories': api.get_user_stories,
    'target': api.change_target,
}

signal.signal(signal.SIGINT, signal_handler)
gnureadline.parse_and_bind("tab: complete")
gnureadline.set_completer(completer)

while True:
    pc.printout("chọn command(list): ", pc.YELLOW)
    cmd = input()

    _cmd = commands.get(cmd)
    
    if _cmd:
        _cmd()    
    elif cmd == "FILE=y":
        api.set_write_file(True)
    elif cmd == "FILE=n":
        api.set_write_file(False)
    elif cmd == "JSON=y":
        api.set_json_dump(True)
    elif cmd == "JSON=n":
        api.set_json_dump(False)
    elif cmd == "":
        print("")
    else:
        pc.printout("Ko tìm thấy giá trị\n", pc.RED)
