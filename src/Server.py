import threading
import socket
import os
import ssl

# TODO: add method to close server (that actually works and doesn't throw an exception)
# TODO: {username} left the chat is not working, need to fix (ngrok issue?)

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best(?) range is 29170 to 29998 [main req is port # > 10,000]

# Implement basic SSL protection with default context
context = ssl.create_default_context()



server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print('Server is online.')

# Make socket secure
secure_server = context.wrap_socket(server, server_side=True_)

# Storing client and username info into lists; should be matching pairs
clients = []
usernames = []

stop_thread = False

# function Broadcast
# Sends a message to all connected clients
def broadcast(message):
	for client in clients:
		client.send(message)

# function Client Connection Handler
# When a client connects to the server, recieve messages from client & send them to all clients (including itself)
def handle(client):
	while True:
		global stop_thread
		if stop_thread == True:
			break
		try:
			# sets message to a recieved message, up to 1024 bytes
			cmd = message = client.recv(1024)

			#checking if message is a command or not
			if cmd.decode('ascii').startswith('KICK'):
				if usernames[clients.index(client)] == 'admin': #checking if the client who sent this message is in the server's database as an admin
					to_be_kicked = cmd.decode('ascii')[5:]
					kick_user(to_be_kicked)
					print(f'{to_be_kicked} was kicked by administrator')
				else:
					client.send('Command was refused!'.encode('ascii'))

			if cmd.decode('ascii').startswith('BAN'):
				if usernames[clients.index(client)] == 'admin':
					to_be_banned = cmd.decode('ascii')[4:]
					kick_user(to_be_banned)
					with open('banlist.txt', 'a') as f: #we store banned users in a text file because we want it to persist
						f.write(f'{to_be_banned}\n')
				else:
					client.send('Command was refused!'.encode('ascii'))

			if cmd.decode('ascii') == ('EXIT'):
				if usernames[clients.index(client)] == 'admin':
					exit_seq()
				else:
					client.send('Command was refused!'.encode('ascii'))

			broadcast(message) #only executes if none of the command code above executes
		except:
			index = clients.index(client)
			clients.remove(client)
			client.close()
			username = usernames[index]
			usernames.remove(username)
			broadcast(f'{username} has left the chat.'.encode('ascii'))
			break

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	while True:
		if stop_thread == True:
			break
		# always running the accept method; if it finds something, return client & address
		client, address = secure_server.accept() 
		print(f'User has connected with IP and port {str(address)}.')
		
		client.send('ID'.encode('ascii'))
		username = client.recv(1024).decode('ascii')

		with open('banlist.txt', 'r') as f:
			bans = f.readlines()
		
		if username+'\n' in bans:
			client.send('BAN'.encode('ascii'))
			client.close()
			continue


		#checking if the user is attempting an Administrator login
		if username == 'admin':
			client.send('PASS'.encode('ascii')) #indicates we want the client to send their password
			password = client.recv(1024).decode('ascii') #assuming the client sends a password back we need to check it
			if password != 'Bouharb': #we should probably find a way to do this that isn't just plaintext in the code :/
				print(f'User on port {str(address)} attempted administrator login unsuccesfully')
				client.send('REFUSE'.encode('ascii'))
				client.close()
				continue #the while true loop needs to continue, but the code below shouldn't execute for an incorrect login, which is why this is here

		usernames.append(username)
		clients.append(client)
		
		print(f'The username of the client is {username}.')
		broadcast(f'{username} has joined the server.'.encode('ascii'))

		# we run one thread for each connected client because they all need to be handled simultaneously
		handle_thread = threading.Thread(target=handle, args=(client,))
		handle_thread.start()

def kick_user(name):
	if name in usernames:
		name_index = usernames.index(name)
		client_to_kick = clients[name_index]
		clients.remove(client_to_kick)
		client_to_kick.send('You were removed from the chat by an administrator'.encode('ascii'))
		usernames.remove(name)
		broadcast(f'{name} was removed by an adnministrator'.encode('ascii'))

def exit_seq():
	print('Initiating exit sequence:')
	for client in clients:
		client_index = clients.index(client)
		client.send('EXIT')
		clients.remove(client)
		usernames.remove(client_index)
	print('Users have been removed succesfully')
	stop_thread = True
	print('Closing server')

receive()