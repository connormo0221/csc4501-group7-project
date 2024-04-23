import threading
import socket
import os

# TODO: add method to close server (that actually works and doesn't throw an exception)
# TODO: {username} left the chat is not working, need to fix (ngrok issue?)

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best(?) range is 29170 to 29998 [main req is port # > 10,000]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print('Server is online.')

# Storing client and username info into lists; should be matching pairs
clients = []
usernames = []
channel = []
strikes = [] # THIS IS GOING TO BE FOR AN AUTOMATED BOUNCER THAT KICKS USERS FOR SPAM (AND MAYBE BANS THEM)
flagged = [] # THIS IS GOING TO BE FOR AN AUTOMATED BOUNCER THAT KICKS USERS FOR SPAM (AND MAYBE BANS THEM)

stop_thread = False

# function Broadcast
# Sends a message to all clients in the same channel as the sender
def broadcast(message, sender):
	for client in clients:
		if channel[client] == channel[sender]:
			client.send(message)

def whisper(sender, targetName, message):
	senderName = usernames[clients.index(sender)]
	target = clients[usernames.index(targetName)]
	tmp = ' '.join(message)
	final_message = (f'{senderName} whispers: {tmp}')
	target.send(final_message.encode('ascii'))

def isAdmin(client):
	if usernames[clients.index(client)] == 'admin':
		return True
	else:
		return False

def join_channel(client, channel_name):
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()

	if channel_name in valid_channels:
		clientIDX = clients[client]
		username = usernames[clientIDX]
		channel[clientIDX] = channel_name
		broadcast(f"{username} has joined {channel_name}")
		client.send(f'You have joined {channel_name} succesfully'.encode('ascii'))
	else:
		client.send('Could not join, channel does not exist'.encode('ascii'))

def create_channel(channel_name):
	with open('channel_list.txt', 'a') as f: #we store channels in a text file because we want it to persist
		f.write(f'{channel_name}\n')

def close_channel(channel_name):
	pass #TODO: IMPLEMENT

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
			# sets message to a recieved message, up to 1024 bytes
			cmd = message = client.recv(1024)

			#checking if message is a command or not
   
			# ADMIN COMMANDS #
			if cmd.decode('ascii').startswith('KICK'): # KICKS A USER FROM THE SERVER #
				if isAdmin(client): #checking if the client who sent this message is in the server's database as an admin
					to_be_kicked = cmd.decode('ascii')[5:]
					kick_user(to_be_kicked)
					print(f'{to_be_kicked} was kicked by administrator')
				else:
					client.send('Command was refused!'.encode('ascii'))

			elif cmd.decode('ascii').startswith('BAN'): # BANS A USER FROM THE SERVER #
				if isAdmin(client):
					to_be_banned = cmd.decode('ascii')[4:]
					kick_user(to_be_banned)
					with open('banlist.txt', 'a') as f: #we store banned users in a text file because we want it to persist
						f.write(f'{to_be_banned}\n')
				else:
					client.send('Command was refused!'.encode('ascii'))
			
			elif cmd.decode('ascii').startswith('MAKE'): # MAKES A NEW SERVER CHANNEL #
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						create_channel(new_channel)
					else:
						client.send('incorrect channel name format, use /help to display valid commands'.encode('ascii'))
				else:
					client.send('Command was refused'.encode('ascii'))
			
			elif cmd.decode('ascii').startswith('CLOSE'): # CLOSES A SERVER CHANNEL #
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						close_channel(new_channel)
					else:
						client.send('incorrect channel name format, use /help to display valid commands'.encode('ascii'))
				else:
					client.send('Command was refused'.encode('ascii'))

			# CLIENT COMMANDS #
			elif cmd.decode('ascii') == ('EXIT'):
				exit_seq(client)
				stop_thread = True

			elif cmd.decode('ascii').startswith('WHISPER'): # MESSAGE A SINGLE PERSON #
				content = (cmd.decode('ascii')[8:]).split()
				target = content[0]
				message = (content[1:])
				sender = client
				whisper(sender, target, message)
			
			elif cmd.decode('ascii').starswith('USERS'): # LIST ALL CONNECTED USERS #
				client.send('Connected Users:\n'.encode('ascii'))
				for username in usernames:
					client.send(f'{username}\n').encode('ascii')
			
			elif cmd.decode('ascii').starswith('CHANNELS'): # LIST ALL CONNECTED USERS #
				client.send('Active channels:\n'.encode('ascii'))
				with open('channel_list.txt', 'r') as c:
					valid_channels = c.readlines()
				tmp = '\n'.join(valid_channels)
				client.send(tmp.encode('ascii'))
				
			
			elif cmd.decode('ascii').startswith('JOIN'):
				chanName = cmd.decode('ascii')[5:]
				if chanName.startswith('#'):
					join_channel(client, chanName)
				else:
					client.send('incorrect channel name format, use /help to display valid commands')


			else:
				broadcast(message.encode('ascii'), client) #only executes if none of the command code above executes
		except:
			index = clients.index(client)
			clients.remove(client)
			client.close()
			username = usernames[index]
			usernames.remove(username)
			broadcast(f'{username} has left the chat.'.encode('ascii'), client)
			break
	# [for debugging thread closure]
	print('handle loop broken succesfully')

def bouncer():
	while True:
		for i in flagged:
			if i:
				kick_user(clients[i])
		


# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	bouncer_thread = threading.Thread(bouncer, daemon = True)
	bouncer_thread.start()
	while True:
		try:
			# always running the accept method; if it finds something, return client & address
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


			#checking if the user is attempting an Administrator login
			if username == 'admin':
				client.send('PASS'.encode('ascii')) #indicates we want the client to send their password
				password = client.recv(1024).decode('ascii') #assuming the client sends a password back we need to check it
				if password != 'Bouharb': #we should probably find a way to do this that isn't just plaintext in the code :/
					print(f'User on {str(address)} attempted administrator login unsuccesfully')
					client.send('REFUSE'.encode('ascii'))
					client.close()
					continue #the while true loop needs to continue, but the code below shouldn't execute for an incorrect login, which is why this is here

			usernames.append(username)
			clients.append(client)
			channel.append('#general') # user will join in the general chat initially
			strikes.append(0) # user will start with no strikes
			flagged.append(False) # users will not be flagged initially
			
			print(f'The username of the client is {username}.')
			broadcast(f'{username} has joined the server.'.encode('ascii'), client)

			# we run one thread for each connected client because they all need to be handled simultaneously
			handle_thread = threading.Thread(target=handle, args=(client,))
			handle_thread.start()
		except:
			print('There was an error recieving client data')

def kick_user(name):
	if name in usernames:
		name_index = usernames.index(name)
		client_to_kick = clients[name_index]
		clients.remove(client_to_kick)
		usernames.remove(name)
		channel.remove[name_index]
		strikes.remove[name_index]
		flagged.remove[name_index]
		client_to_kick.send('You were removed from the chat'.encode('ascii'))
		client_to_kick.send('KICKED'.encode('ascii'))
		broadcast(f'{name} was removed from the chat'.encode('ascii'), client_to_kick) # TODO: FIX THIS, IT WILL BROADCAST THIS MESSAGE TO NOBODY

def exit_seq(client):
	clientidx = clients.index(client)
	name = usernames[clientidx]
	clients.remove(client)
	usernames.remove(name)
	channel.remove[clientidx]
	strikes.remove[clientidx]
	flagged.remove[clientidx]
	broadcast(f'{name} has left the server'.encode('ascii'), client) # TODO: FIX THIS, IT WILL BROADCAST THIS MESSAGE TO NOBODY
	client.send('EXIT'.encode('ascii'))

receive()