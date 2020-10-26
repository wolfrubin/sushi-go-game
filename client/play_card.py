"""This module is for manually testing the game client.

Run a python shell
from game_client import *
and then run create_game() to create a game etc
"""

import socket


def get_game(name):
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    if name == 'c':
        srvsock.send('SuGo 1.0\r\nGAME_STATE\r\nfun game\r\nchristian\r\n''\r\n\r\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('SuGo 1.0\r\nGAME_STATE\r\nfun game\r\nbrandon\r\n''\r\n\r\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data

def play_card(name):
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    if name == 'c':
        srvsock.send('SuGo 1.0\r\nPLAY_CARD\r\nfun game\r\nchristian\r\n0\r\n\r\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('SuGo 1.0\r\nPLAY_CARD\r\nfun game\r\nbrandon\r\n0\r\n\r\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data


play_card('c')
play_card('b')

get_game('c')
get_game('b')
