import threading
import socket

# set client username
username = input("Type in a username: ")

# set host and port
# TODO: add proper type checking
host = input("Type in the host address: ")
port = input("Type in the host port: ")

# connecting the client to a host & port; dependent on user input
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

# Recieve function for data from the server
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
			print("An error occured, closing connection!")
			client.close()
			break

# Send messages to the server
def write():
	while True:
		message = (f'{username}: {input("")}')
		# constantly running user input function and as soon as enter is hit it sends a message and prompts for a new message
		client.send(message.encode('ascii'))
		
# These each need their own thread since it needs to send and receive simulatenously
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()