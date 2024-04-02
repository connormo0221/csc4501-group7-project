import threading
import socket
import os

# TODO: {username} left the chat is not working, need to fix
# related to above: clients & usernames are not being removed when they disconnect
# TODO: remove plaintext admin password, replace w/ secure version
# TODO: add support for multiple administrator accounts
# TODO: optimize the admin check when parsing commands
# TODO: fix exit_seq() breaking the handle loop but not the receive loop

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best range is 29170 to 29998 [main req. is port # > 10,000]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print('Server is online.')

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
# When a client connects to the server, receive messages from client & send them to all clients (including itself)
def handle(client):
	while True:
		global stop_thread

		if stop_thread == True:
			# for debugging thread closure:
			print('DEBUG_SERVER: breaking handle loop')
			break
		
		try:
			# sets message to a received message, up to 1024 bytes
			cmd = message = client.recv(1024)

			# checking if message is a command or not
			if cmd.decode('ascii').startswith('KICK'):
				if usernames[clients.index(client)] == 'admin': # checking if the client who sent this message is in the server's database as an admin
					to_be_kicked = cmd.decode('ascii')[5:]
					kick_user(to_be_kicked)
					print(f'{to_be_kicked} was kicked by an administrator.')
				else:
					client.send('Command was refused!'.encode('ascii'))
			elif cmd.decode('ascii').startswith('BAN'):
				if usernames[clients.index(client)] == 'admin':
					to_be_banned = cmd.decode('ascii')[4:]
					kick_user(to_be_banned)
					with open('banlist.txt', 'a') as f: # we store banned users in a text file because we want it to persist
						f.write(f'{to_be_banned}\n')
				else:
					client.send('Command was refused!'.encode('ascii'))
			elif cmd.decode('ascii') == ('CLOSE'):
				if usernames[clients.index(client)] == 'admin':
					exit_seq()
					stop_thread = True
				else:
					client.send('Command was refused!'.encode('ascii'))
			elif cmd.decode('ascii') == ('LIST'):
				client.send(f'Users currently connected: \n {usernames}'.encode('ascii'))
			else:
				broadcast(message) # only executes if none of the command code above executes
		except:
			index = clients.index(client)
			clients.remove(client)
			client.close()
			username = usernames[index]
			usernames.remove(username)
			broadcast(f'{username} has left the chat.'.encode('ascii'))
			stop_thread == True

	# for debugging thread closure:
	print('DEBUG_SERVER: handle loop broken succesfully')

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	while True:
		global stop_thread

		if stop_thread == True:
			# for debugging thread closure:
			print('DEBUG_SERVER: breaking receive loop')
			break

		try:
			# always running the accept method; if it finds something, return client & address
			client, address = server.accept() 
			#if stop_thread == True: # skip to next loop & break
			#	continue
			print(f'User has connected with IP and port {str(address)}.')
			client.send('ID'.encode('ascii'))
			username = client.recv(1024).decode('ascii')

			with open('banlist.txt', 'r') as f:
				bans = f.readlines()
			
			if username+'\n' in bans:
				client.send('BAN'.encode('ascii'))
				client.close()
				continue

			# checking if the user is attempting to login as an administrator
			if username == 'admin':
				client.send('PASS'.encode('ascii')) # indicates we want the client to send their password
				password = client.recv(1024).decode('ascii') # assuming the client sends a password back we need to check it
				if password != 'Bou-Harb':
					print(f'User with IP and port {str(address)} failed to login as an administrator.')
					client.send('REFUSE'.encode('ascii'))
					client.close()
					continue # the while loop needs to continue, but the code below shouldn't execute for an incorrect login, which is why this is here

			usernames.append(username)
			clients.append(client)
			
			print(f'The username of the client is {username}.')
			broadcast(f'{username} has joined the server.'.encode('ascii'))

			# we run one thread for each connected client because they all need to be handled simultaneously
			handle_thread = threading.Thread(target=handle, args=(client,))
			handle_thread.start()
		
		except:
			if client:
				client.send('There was an error establishing your connection.'.encode('ascii'))
				client.send('KICKED'.encode('ascii'))
	
	# for debugging thread closure:
	print('DEBUG_SERVER: receive loop broken succesfully')

def kick_user(name):
	if name in usernames:
		name_index = usernames.index(name)
		client_to_kick = clients[name_index]
		clients.remove(client_to_kick)
		usernames.remove(name)
		client_to_kick.send('You were removed from the chat by an administrator.'.encode('ascii'))
		client_to_kick.send('KICKED'.encode('ascii'))
		broadcast(f'{name} was removed by an administrator.'.encode('ascii'))

def exit_seq():
	print('Initiating server shutdown sequence:')
	print(f'Currently connected \n {usernames}')
	while usernames:
		print(f'Removing {usernames[0]}.')
		client_to_kick = clients[0]
		clients.remove(client_to_kick)
		del usernames[0]
		client_to_kick.send('CLOSE'.encode('ascii'))
	print('Users have been removed succesfully.')
	#server.connect((host, int(port))) # connect to server locally in order to stop the receive() thread

receive()
os._exit(0) # close program when all threads are finished