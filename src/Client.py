import threading
import socket
import os

# TODO: add proper type checking for host & port variables
# TODO: add error handling to failed connections
# TODO: fix formatting; submitted messages are inserted between unsent messages

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')

# Allow client to set server host IP & port number
host = input('Type in the host address: ')
port = input('Type in the host port: ')

# Connect the client to a host IP & port number; dependent on previous user input
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

# function Receive
# Receives & decodes data from the server; if data can't be decoded, client disconnects
def receive():
	while True:
		try:
			message = client.recv(1024).decode('ascii')
			# the server uses a client to send messages which is why client is here
			if message == 'ID':
				client.send(username.encode('ascii'))
			else:
				print(message)
		except:
			print('Data transfer stopped, closing connection.')
			client.close()
			os._exit(1)

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	# User input function is always running in order to catch input
	while True:	
		raw = input('')
		if raw == '/exit':
			print('Exiting the server...')
			client.close()
			os._exit(1)
		else:
			message = (f'{username}: {raw}')
			client.send(message.encode('ascii'))
		
# Both functions need their own thread since we need to be able to send & recieve messages simultaneously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()