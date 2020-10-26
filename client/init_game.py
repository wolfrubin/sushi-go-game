"""
Run a python shell
from game_client import *
and then run create_game() to create a game etc
"""

import socket



create_instruction = 'SuGo 1.0\r\nCREATE_GAME\r\nfun game\r\nchristian\r\n''\r\n\r\n'.encode('utf-8')
get_instruction = 'SuGo 1.0\r\nGAME_STATE\r\nfun game\r\nchristian\r\n''\r\n\r\n'.encode('utf-8')
join_instruction = 'SuGo 1.0\r\nJOIN_GAME\r\nfun game\r\nbrandon\r\n''\r\n\r\n'.encode('utf-8')
start_instruction = 'SuGo 1.0\r\nSTART_GAME\r\nfun game\r\nchristian\r\n''\r\n\r\n'.encode('utf-8')
play_instruction = 'SuGo 1.0\r\nPLAY_CARD\r\nfun game\r\nchristian\r\n0\r\n\r\n'.encode('utf-8')

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
        srvsock.send('SuGo 1.0\r\nGAME_STATE\r\nfun game\r\nchristian\r\n''\r\n\r\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('SuGo 1.0\r\nGAME_STATE\r\nfun game\r\nbrandon\r\n''\r\n\r\n'.encode('utf-8'))
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
        srvsock.send('SuGo 1.0\r\nPLAY_CARD\r\nfun game\r\nchristian\r\n0\r\n\r\n'.encode('utf-8'))
    elif name == 'b':
        srvsock.send('SuGo 1.0\r\nPLAY_CARD\r\nfun game\r\nbrandon\r\n0\r\n\r\n'.encode('utf-8'))
    data = srvsock.recv(4096) 
    print "received message:", data

def init_game():
    create_game()
    join_game()
    start_game()


init_game()