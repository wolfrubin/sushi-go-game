"""This module is for manually testing the game client.

Run a python shell
from game_client import *
and then run create_game() to create a game etc
"""

import socket


get_instruction = 'GAME_STATE\n\nfun game\n\nchristian\n\n'.encode('utf-8')
play_instruction = 'PLAY_CARD\n\nfun game\n\nchristian\n\n0'.encode('utf-8')

def get_game(name):
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    if name == 'c':
        srvsock.send('GAME_STATE\n\nfun game\n\nchristian\n\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('GAME_STATE\n\nfun game\n\nbrandon\n\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data

def play_card(name):
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    if name == 'c':
        srvsock.send('PLAY_CARD\n\nfun game\n\nchristian\n\n0\n\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('PLAY_CARD\n\nfun game\n\nbrandon\n\n0\n\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data

play_card('c')
play_card('b')

get_game('c')
get_game('b')
