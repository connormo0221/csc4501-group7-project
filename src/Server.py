import threading
import socket
import os

# TODO: add method to close server (that actually works and doesn't throw an exception)
# TODO: {username} left the chat is not working, need to fix (ngrok issue?)

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best(?) range is 29170 to 29998

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print('Server is online.')

# Storing client and username info into lists; should be matching pairs
clients = []
usernames = []

# function Broadcast
# Sends a message to all connected clients
def broadcast(message):
	for client in clients:
		client.send(message)

# function Client Connection Handler
# When a client connects to the server, recieve messages from client & send them to all clients (including itself)
def handle(client):
	while True:
		try:
			# sets message to a recieved message, up to 1024 bytes
			message = client.recv(1024)
			broadcast(message)
		except:
			index = clients.index(client)
			clients.remove(client)
			client.close()
			username = usernames[index]
			usernames.remove(username)
			broadcast(f'{username} has left the chat.'.encode('ascii'))
			break

# function Command
# Adds server-side commands for closing the server, viewing connected clients, etc.
def command():
	while True:
		command = input('')
		if command == "/exit":
			print('Disconnecting clients...')
			for client in clients:
				index = clients.index(client)
				clients.remove(client)
				client.close()
				username = usernames[index]
				usernames.remove(username)
			print('Closing server...')
			os._exit(1)
		elif command == '/view':
			print('Clients connected:')
			for client in clients:
				index = clients.index(client)
				username = usernames[index]
				print(f'{username} is connected.')
		elif command == '/help':
			print('Server commands: /exit, /view.')
		else:
			print('Invalid command. Use /help to display available commands.')

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	while True:
		# command thread needed to catch text input
		command_thread = threading.Thread(target=command)
		command_thread.start()

		# always running the accept method; if it finds something, return client & address
		client, address = server.accept() 
		print(f'User has connected with IP and port {str(address)}.')
		
		client.send('ID'.encode('ascii'))
		username = client.recv(1024).decode('ascii')
		usernames.append(username)
		clients.append(client)
		
		print(f'The username of the client is {username}.')
		broadcast(f'{username} has joined the server.'.encode('ascii'))

		# we run one thread for each connected client because they all need to be handled simultaneously
		handle_thread = threading.Thread(target=handle, args=(client,))
		handle_thread.start()

receive()