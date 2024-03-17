import threading
import socket

# TODO: add method to close client

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')

# Allow client to set server host IP & port number
# TODO: add proper type checking
host = input('Type in the host address: ')
port = input('Type in the host port: ')

# Connect the client to a host IP & port number; dependent on previous user input
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

# function Receive
# Receives & decodes data from the server; if any message can't be decoded, client disconnects
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
			print('An error occured, closing connection!')
			client.close()
			break

# Send messages to the server
def write(): # TODO: fix formatting; submitted messages are inserted between unsent messages
	while True:
		message = (f'{username}: {input('')}')
		# User input function is always running in order to catch 'enter' key presses;
		# Upon pressing enter, the current text is sent as a message to the server and another prompt is shown
		client.send(message.encode('ascii'))
		
# Both functions need their own thread since we need to be able to send & recieve messages simultaneously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()