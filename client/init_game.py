"""
Run a python shell
from game_client import *
and then run create_game() to create a game etc
"""

import socket



create_instruction = 'CREATE_GAME\n\nfun game\n\nchristian\n\n'.encode('utf-8')
get_instruction = 'GAME_STATE\n\nfun game\n\nchristian\n\n'.encode('utf-8')
join_instruction = 'JOIN_GAME\n\nfun game\n\nbrandon\n\n'.encode('utf-8')
start_instruction = 'START_GAME\n\nfun game\n\nchristian\n\n'.encode('utf-8')
play_instruction = 'PLAY_CARD\n\nfun game\n\nchristian\n\n0'.encode('utf-8')

def create_game():
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    srvsock.send(create_instruction)
    data = srvsock.recv(4096) 
    print "received message:", data

def get_game(name):
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    if name == 'c':
        srvsock.send('GAME_STATE\n\nfun game\n\nchristian\n\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('GAME_STATE\n\nfun game\n\nbrandon\n\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data

def join_game():
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    srvsock.send(join_instruction)
    data = srvsock.recv(4096) 
    print "received message:", data

def start_game():
    srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvsock.connect(('localhost', 4136))
    srvsock.send(start_instruction)
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

def init_game():
    create_game()
    join_game()
    start_game()


init_game()