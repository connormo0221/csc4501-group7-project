import threading
import socket

# TODO: add method to close server

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
			broadcast(f'{username} has left the chat.'.encode('ascii')) # TODO: not working, fix (ngrok issue?)
			break

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	while True:
		# always running the accept method; if it finds something, return client & address
		client, address = server.accept() 
		print(f'User has connected with IP and port {str(address)}.')
		
		client.send('ID'.encode('ascii'))
		username = client.recv(1024).decode('ascii')
		usernames.append(username)
		clients.append(client)
		
		print(f'The username of the client is {username}.')
		client.send(f'---\nSuccessfully connected to the server!\n---'.encode('ascii'))
		broadcast(f'{username} has joined the server.'.encode('ascii'))
		
		# we run one thread for each connected client because they all need to be handled simultaneously
		thread = threading.Thread(target=handle, args=(client,))
		thread.start()

receive()