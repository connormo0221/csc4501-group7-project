import threading
import socket
import os

# TODO: add proper type checking for host & port variables
# TODO: add error handling to failed connections
# TODO: fix formatting; submitted messages are inserted between unsent messages (wait for GUI?)
# TODO: fix clients not closing after server failure (write thread isn't closing)

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
			# for debugging thread closure:
			print('DEBUG_CLIENT: breaking receive loop')
			break
		
		try:
			message = client.recv(1024).decode('ascii') # the server uses a client to send messages
			if message == 'ID':
				client.send(username.encode('ascii'))
				next_msg = client.recv(1024).decode('ascii')
				if next_msg == 'PASS': # server is asking for a password
					client.send(password.encode('ascii'))
					if client.recv(1024).decode('ascii') == 'REFUSE': # server responded with connection refused message
						raise RuntimeError('Connection refused, reason: Incorrect password.')
				elif next_msg == 'BAN': # server responded with ban message
					raise RuntimeError('Connection refused, reason: You have been banned by an administrator.')
			elif message == 'KICKED': # server responded with kick message
				raise RuntimeError('Connection refused, reason: You have been kicked by an administrator.')
			elif message == 'CLOSE': # server responded with close message
				raise RuntimeError('Connection refused, reason: A server administrator has closed the room.')
			else:
				print(message)
		except:
			print('Data transfer stopped, closing connection.')
			client.close()
			stop_thread = True

	# for debugging thread closure:
	print('DEBUG_CLIENT: receive loop broken')

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	# User input function is always running in order to catch input
	while True:
		global stop_thread 

		if stop_thread:
			# for debugging thread closure:
			print('DEBUG_CLIENT: breaking write loop')
			break

		try:
			message = (f'{username}: {input("")}')

			if message[len(username)+2:].startswith('/'): # checks if the message being sent has a '/' at the start of it (indicates a command)
				if (username == 'admin'):
					# available commands (admin): KICK, BAN, CLOSE
					if message[len(username)+2:].startswith('/kick'):
						print(f'Kicking {message[len(username)+2+6:]} from the server.')
						client.send(f'KICK {message[len(username)+2+6:]}'.encode('ascii'))
					elif message[len(username)+2:].startswith('/ban'):
						print(f'Banning {message[len(username)+2+6:]} from the server.')
						client.send(f'BAN {message[len(username)+2+5:]}'.encode('ascii'))
					elif message[len(username)+2:].startswith('/close'):
						print('Attempting to close the server.')
						client.send(f'CLOSE'.encode('ascii'))
						stop_thread = True
						continue
				# available commands (non-admin): EXIT (or QUIT), LIST
				if message[len(username)+2:].startswith('/exit') | message[len(username)+2:].startswith('/quit'):
					print('Leaving the server.')
					stop_thread = True
				elif message[len(username)+2:].startswith('/list'):
					client.send(f'LIST'.encode('ascii'))
				else:
					print('Invalid command.')
			else:
				client.send(message.encode('ascii'))
		except:
			print('Error: Unable to send message.')
			stop_thread = True
	
	# for debugging thread closure:
	print('DEBUG_CLIENT: write loop broken')
		
# Both functions need their own thread since we need to be able to send & receive messages simultaneously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

if receive_thread.is_alive() == False & write_thread.is_alive() == False:
	os._exit(0) # close program after threads are closed