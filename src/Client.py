import threading
import socket
import os

# TODO: add proper type checking for host & port variables
# TODO: add error handling to failed connections
# TODO: fix formatting; submitted messages are inserted between unsent messages

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')
if username == 'admin':
	password = input('Type in a password: ')

# Allow client to set server host IP & port number
host = input('Type in the host address: ')
port = input('Type in the host port: ')

# Connect the client to a host IP & port number; dependent on previous user input
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

stop_thread = False

# function Receive
# Receives & decodes data from the server; if data can't be decoded, client disconnects
def receive():
	while True:
		global stop_thread
		if stop_thread == True:
			# [for debugging thread closure]
			# print('breaking receive loop')
			break
		try:
			message = client.recv(1024).decode('ascii')
			# the server uses a client to send messages which is why client is here
			if message == 'ID':
				client.send(username.encode('ascii'))
				next_msg = client.recv(1024).decode('ascii')
				if next_msg == 'PASS':
					client.send(password.encode('ascii'))
					if client.recv(1024).decode('ascii') == 'REFUSE':
						print('Connection was refused, incorrect password')
						stop_thread = True
				elif next_msg == 'BAN':
					print('Connection refused: you have been banned by an administrator')
					client.close()
					stop_thread = True
			elif message == 'KICKED':
				client.close()
				stop_thread = True
			elif message == 'EXIT':
				print('The server administrator has closed the room')
				stop_thread = True
			else:
				print(message)
		except:
			print('Data transfer stopped, closing connection.')
			client.close()
	# [for debugging thread closure]
	# print('receive loop broken')

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	# User input function is always running in order to catch input
	while True:
		if stop_thread:
			# [for debugging thread closure]
			#print('breaking write loop')
			break
		try:
			message = (f'{username}: {input("")}')

			if message[len(username)+2:].startswith('/'): #checks if the message being sent has a '/' at the start of it (indicates a command)
				if (username == 'admin'):
					#three commands KICK, BAN, EXIT
					if message[len(username)+2:].startswith('/kick'):
						print(f'kicking {message[len(username)+2+6:]} from the server')
						client.send(f'KICK {message[len(username)+2+6:]}'.encode('ascii'))
					elif message[len(username)+2:].startswith('/ban'):
						print(f'Banning {message[len(username)+2+6:]} from the server')
						client.send(f'BAN {message[len(username)+2+5:]}'.encode('ascii'))
					elif message[len(username)+2:].startswith('/exit'):
						print('sending exit command')
						client.send(f'EXIT'.encode('ascii'))
				else:
					print('commands may only be executed by the administrator')

			else:
				client.send(message.encode('ascii'))
		except:
			print('unable to send message')
	# [for debugging thread closure]
	# print('write loop broken')
		
# Both functions need their own thread since we need to be able to send & recieve messages simultaneously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()