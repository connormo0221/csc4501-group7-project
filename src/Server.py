import threading
import socket
import os

# TODO: add method to close server (that actually works and doesn't throw an exception)

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best(?) range is 29170 to 29998 [main req is port # > 10,000]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print('Server is online.')

# Storing connected client info into lists; a single index value should correspond to a user in all lists
clients = [] # stores (host, port) pairs
usernames = [] # stores client usernames
channel = [] # stores the name of the user's current channel
strikes = [] # stores the number of strikes a user has

stop_thread = False

# Default communication method
# Sends a message to all clients in the same channel as the sender
def broadcast(message, sender_channel):
	for client in clients:
		if channel[client] == sender_channel:
			client.send(message)

# Checks if a client has administrator privileges
def isAdmin(client):
	if usernames[clients.index(client)] == 'admin':
		return True
	else:
		return False
	
# Daemon function that checks the strikes list and kicks a user if the number is >= 5
def bouncer():
	while True:
		for i in strikes:
			if i >= 5:
				kick_user(clients[i])

# Kicks a user from the server
def kick_user(name):
	if name in usernames:
		name_index = usernames.index(name)
		client_to_kick = clients[name_index] # Use index to get client info
		curr_channel = channel[name_index] # Use index to find user's current channel
		del clients[name_index]
		del usernames[name_index]
		del channel[name_index]
		del strikes[name_index]
		client_to_kick.send('You were removed from the chat.'.encode('ascii'))
		client_to_kick.send('KICKED'.encode('ascii')) # Tell client to disconnect via KICKED message
		broadcast(f'{name} was removed from the chat.'.encode('ascii'), curr_channel)

# Kicks a user from the server and then adds their name to the banlist
def ban_user(to_be_banned, client):
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if to_be_banned in banned_users:
		client.send('ERROR: This user has already been banned.'.encode('ascii'))
	else:
		kick_user(to_be_banned)
		with open('banlist.txt', 'w') as w: # Storing in a text file for continuity
			w.write(f'{to_be_banned}\n')

# Removes a username from the banlist, if present
def unban_user(to_be_unbanned, client):
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if to_be_unbanned in banned_users:
		with open('banlist.txt', 'w') as w:
			for line in banned_users:
				if line.strip('\n') != to_be_unbanned:
					w.write(line)
	else:
		client.send('ERROR: This user is not currently banned.'.encode('ascii'))

# Creates a new text channel
def create_channel(channel_name, client):
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()
	if channel_name in valid_channels:
		client.send('ERROR: Channel already exists.'.encode('ascii'))
	else:
		with open('channel_list.txt', 'a') as f: # Storing in a text file for continuity
			f.write(f'{channel_name}\n')

# Closes a text channel by moving all users to general and then removing it from the channel list
def close_channel(channel_name, client):
	with open('channel_list.txt', 'r') as r:
		valid_channels = r.readlines()
	if channel_name in valid_channels:
		for c in channel:
			if c == channel_name:
				c = '#general'
		with open('channel_list.txt', 'w') as w:
			for line in valid_channels:
				if line.strip('\n') != channel_name:
					w.write(line)
	else:
		client.send('ERROR: Cannot remove a channel that does not exist.'.encode('ascii'))

# Method for exiting the server
def exit_seq(client):
	client_index = clients.index(client) # Get a client's index via their (host, port) pair
	name = usernames[client_index] # Use index to get client name for broadcast
	curr_channel = channel[client_index] # Use index to get current channel for broadcast
	del clients[client_index]
	del usernames[client_index]
	del channel[client_index]
	del strikes[client_index]
	broadcast(f'{name} has left the server.'.encode('ascii'), curr_channel)
	client.send('EXIT'.encode('ascii'))

# Sends a message to a specific user
def whisper(sender, target, message):
	if target in usernames:
		sender_name = usernames[clients.index(sender)]
		target_user = clients[usernames.index(target)]
		tmp = ' '.join(message) # Convert split message back into a string
		target_user.send(f'{sender_name} whispers: {tmp}'.encode('ascii'))
	else:
		sender.send('ERROR: This user is not currently online.'.encode('ascii'))

# Move client to a specified channel
def join_channel(client, channel_name):
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()
	if channel_name in valid_channels:
		client_index = clients[client]
		username = usernames[client_index]
		channel[client_index] = channel_name
		broadcast(f"{username} has joined {channel_name}", channel_name)
		client.send(f'You have joined {channel_name} succesfully.'.encode('ascii'))
	else:
		client.send('ERROR: Channel does not exist.'.encode('ascii'))


# function Client Connection Handler
# When a client connects to the server, recieve messages from client & send them to all clients (including itself)
def handle(client):
	while True:
		global stop_thread
		if stop_thread == True:
			# [for debugging thread closure]
			print('breaking handle loop')
			break
			
		try:
			# Sets message to a recieved message, up to 1024 bytes
			cmd = message = client.recv(1024)
   
			# Check using keywords if a message is a command
			## ADMIN COMMANDS ##
			if cmd.decode('ascii').startswith('KICK'): # KICKS A USER FROM THE SERVER
				if isAdmin(client):
					to_be_kicked = cmd.decode('ascii')[5:]
					kick_user(to_be_kicked)
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))

			elif cmd.decode('ascii').startswith('BAN'): # BANS A USER FROM THE SERVER
				if isAdmin(client):
					to_be_banned = cmd.decode('ascii')[4:]
					ban_user(to_be_banned, client)
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))

			elif cmd.decode('ascii').startswith('UNBAN'): # UNBANS A USER FROM THE SERVER
				if isAdmin(client):
					to_be_unbanned = cmd.decode('ascii')[6:]
					unban_user(to_be_unbanned, client)
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))
			
			elif cmd.decode('ascii').startswith('MAKE'): # MAKES A NEW SERVER CHANNEL
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						create_channel(new_channel, client)
					else:
						client.send('ERROR: Invalid channel name format, use /help to display valid commands.'.encode('ascii'))
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))
			
			elif cmd.decode('ascii').startswith('CLOSE'): # CLOSES A SERVER CHANNEL
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						close_channel(new_channel, client)
					else:
						client.send('ERROR: Invalid channel name format, use /help to display valid commands.'.encode('ascii'))
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))

			## CLIENT COMMANDS ##
			elif cmd.decode('ascii') == ('EXIT'): # EXITS THE SERVER
				exit_seq(client)
				stop_thread = True

			elif cmd.decode('ascii').startswith('WHISPER'): # MESSAGE A SPECIFIC PERSON
				content = (cmd.decode('ascii')[8:]).split()
				target = content[0]
				message = (content[1:])
				sender = client
				whisper(sender, target, message)
			
			elif cmd.decode('ascii').starswith('USERS'): # LIST ALL CONNECTED USERS
				client.send('Connected users:\n'.encode('ascii'))
				for username in usernames:
					client.send(f'{username}\n').encode('ascii')
			
			elif cmd.decode('ascii').starswith('CHANNELS'): # LIST ALL ACTIVE CHANNELS
				client.send('Active channels:\n'.encode('ascii'))
				with open('channel_list.txt', 'r') as c:
					valid_channels = c.readlines()
				tmp = '\n'.join(valid_channels)
				client.send(tmp.encode('ascii'))
				
			elif cmd.decode('ascii').startswith('JOIN'): # JOIN A NEW CHANNEL
				chanName = cmd.decode('ascii')[5:]
				if chanName.startswith('#'):
					join_channel(client, chanName)
				else:
					client.send('ERROR: Incorrect channel name format, use /help to display valid commands.'.encode('ascii'))

			else: # Only executes if no commands were used
				client_index = clients(client)
				curr_channel = channel[client_index]
				broadcast(message.encode('ascii'), curr_channel)
		except:
			exit_seq(client) # Start exit sequence if an exception occurs
			break		

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	bouncer_thread = threading.Thread(bouncer, daemon = True)
	bouncer_thread.start()

	while True:
		try:
			# Always running the accept method; if it finds something, return client & address
			client, address = server.accept() 
			print(f'User has connected with IP and port {str(address)}.')
			client.send('ID'.encode('ascii'))
			username = client.recv(1024).decode('ascii')

			with open('banlist.txt', 'r') as f:
				bans = f.readlines()
			
			if username+'\n' in bans:
				client.send('BAN'.encode('ascii'))
				client.close()
				continue

			# Checking if the user is attempting to login as an administrator
			if username == 'admin':
				client.send('PASS'.encode('ascii')) # Indicates we want the client to send their password
				password = client.recv(1024).decode('ascii') # Assuming the client sends a password back we need to check it
				if password != 'Bouharb': # TODO: Remove plaintext admin password
					print(f'User on {str(address)} attempted administrator login unsuccesfully')
					client.send('REFUSE'.encode('ascii'))
					client.close()
					continue # The while-true loop needs to continue, but the code below shouldn't execute for an incorrect login, which is why this is here

			usernames.append(username)
			clients.append(client)
			channel.append('#general') # Users are in general chat by default upon joining
			strikes.append(0) # User will start with no strikes
			
			print(f'The username of the client is {username}.')
			broadcast(f'{username} has joined the server.'.encode('ascii'), '#general')

			# We run one thread for each connected client because they all need to be handled simultaneously
			handle_thread = threading.Thread(target=handle, args=(client,))
			handle_thread.start()
		except:
			print('There was an error recieving client data')

receive()