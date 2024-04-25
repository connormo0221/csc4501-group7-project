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

stop_thread = False

# default communication method,
# Sends a message to all clients in the same channel as the sender
def broadcast(message, sender_channel):
	for client in clients:
		clientidx = clients.index(client)
		if channel[clientidx] == sender_channel:
			client.send(message)

#helper function to check if client is actually an admin when sending admin commands
def isAdmin(client):
	if usernames[clients.index(client)] == 'admin':
		return True
	else:
		return False
	
# daemon function
# continually checks for any value in the strikes list, greater than 5
# if it finds one, it kicks the associated user
def bouncer():
	while True:
		for i in strikes:
			if i >= 5:
				kick_user(clients[i])

# kicks a user from the server
def kick_user(name):
	if name in usernames:
		name_index = usernames.index(name)
		client_to_kick = clients[name_index]
		curChan = channel[name_index]
		clients.remove(client_to_kick)
		usernames.remove(name)
		channel.remove[name_index]
		strikes.remove[name_index]
		client_to_kick.send('You were removed from the chat'.encode('ascii'))
		client_to_kick.send('KICKED'.encode('ascii'))
		broadcast(f'{name} was removed from the chat'.encode('ascii'), curChan)

# kicks a user from the server and then adds their name to the banlist
def ban_user(to_be_banned, client):
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if to_be_banned in banned_users:
		client.send('ERROR: This user has already been banned')
	else:
		kick_user(to_be_banned)
		with open('banlist.txt', 'w') as w:
			w.write(f'{to_be_banned}\n')

# removes a username from the banlist, if present
def unban_user(to_be_unbanned, client):
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if to_be_unbanned in banned_users:
		with open('banlist.txt', 'w') as w:
			for line in banned_users:
				if line.strip('\n') != to_be_unbanned:
					w.write(line)
	else:
		client.send('ERROR: This user is not currently banned')

# creates a new channel
def create_channel(channel_name, client):
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()
	if channel_name in valid_channels:
		client.send('Channnel already exists'.encode('ascii'))
	else:
		with open('channel_list.txt', 'a') as f: #we store channels in a text file because we want it to persist
			f.write(f'{channel_name}\n')

# moves all users in a channel to general
# then removes the channel from the list of 
# valid channels
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
		client.send('Cannot remove a channel that does not exist')

# method for exiting the server
def exit_seq(client):
	clientidx = clients.index(client)
	name = usernames[clientidx]
	curChan = channel[clientidx]
	clients.remove(client)
	usernames.remove(name)
	channel.remove[clientidx]
	strikes.remove[clientidx]
	broadcast(f'{name} has left the server'.encode('ascii'), curChan)
	client.send('EXIT'.encode('ascii'))

# Sends a message to a specific user
def whisper(sender, targetName, message):
	if targetName in usernames:
		senderName = usernames[clients.index(sender)]
		target = clients[usernames.index(targetName)]
		tmp = ' '.join(message)
		final_message = (f'{senderName} whispers: {tmp}')
		target.send(final_message.encode('ascii'))
	else:
		sender.send('Whisper Failed: This user is not currently online'.encode('ascii'))

# join a given channel
def join_channel(client, channel_name):
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()

	if channel_name in valid_channels:
		clientIDX = clients[client]
		username = usernames[clientIDX]
		channel[clientIDX] = channel_name
		broadcast(f"{username} has joined {channel_name}", channel_name)
		client.send(f'You have joined {channel_name} succesfully'.encode('ascii'))
	else:
		client.send('Could not join, channel does not exist'.encode('ascii'))

def transfer_request(hostname, clientname, filename):
	client = clients[usernames.index(clientname)]
	client.send(f'FTP_REQ {hostname} {filename}')
	response = client.recv(1024).decode('ascii')
	if response == 'y':
		return True
	else:
		return False

def intermediate_file_acc(client):
	client.send('FTP CONF'.encode('ascii'))
	file_name = client.recv(1024).decode()
	file_size = client.recv(1024).decode()
	file = open(file_name, 'wb')
	file_bytes = b""
	done = False
	while not done:
		data = client.recv(1024)
		if file_bytes[-5:] == b"<END>":
			done = True
		else:
			file_bytes += data
	file.write(file_bytes)
	file.close()

def transfer_file(filename, target):
	f = open(filename, 'rb')
	f_size = os.path.getsize(filename)
	client = clients[usernames.index(target)]
	client.send(filename.encode())
	client.send(str(f_size).encode())
	data = f.read()
	client.sendall(data)
	client.send(b"<END>")
	f.close()

def rm_local(filename):
	if os.path.exists(filename):
		os.remove(filename)
	else:
		print(f'file deletion was attempted on filename [{filename}] but no such file exists')

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
   
			## ADMIN COMMANDS ##
			if cmd.decode('ascii').startswith('KICK'): # KICKS A USER FROM THE SERVER #
				if isAdmin(client): #checking if the client who sent this message is in the server's database as an admin
					to_be_kicked = cmd.decode('ascii')[5:]
					kick_user(to_be_kicked)
				else:
					client.send('Command was refused!'.encode('ascii'))

			# BANS A USER FROM THE SERVER #
			elif cmd.decode('ascii').startswith('BAN'):
				if isAdmin(client):
					to_be_banned = cmd.decode('ascii')[4:]
					ban_user(to_be_banned, client)
				else:
					client.send('Command was refused!'.encode('ascii'))

			# UNBANS A USER FROM THE SERVER #
			elif cmd.decode('ascii').startswith('UNBAN'):
				if isAdmin(client):
					to_be_unbanned = cmd.decode('ascii')[6:]
					unban_user(to_be_unbanned, client)
				else:
					client.send('Command was refused!'.encode('ascii'))
			
			# MAKES A NEW SERVER CHANNEL #
			elif cmd.decode('ascii').startswith('MAKE'):
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						create_channel(new_channel, client)
					else:
						client.send('incorrect channel name format, use /help to display valid commands'.encode('ascii'))
				else:
					client.send('Command was refused'.encode('ascii'))
			
			# CLOSES A SERVER CHANNEL #
			elif cmd.decode('ascii').startswith('CLOSE'):
				if isAdmin(client):
					new_channel = cmd.decode('ascii')[5:]
					if new_channel.startswith('#'):
						close_channel(new_channel, client)
					else:
						client.send('incorrect channel name format, use /help to display valid commands'.encode('ascii'))
				else:
					client.send('Command was refused'.encode('ascii'))

			## CLIENT COMMANDS ##
			elif cmd.decode('ascii') == ('EXIT'):
				exit_seq(client)
				stop_thread = True

			# MESSAGE A SINGLE PERSON #
			elif cmd.decode('ascii').startswith('WHISPER'):
				content = (cmd.decode('ascii')[8:]).split()
				target = content[0]
				message = (content[1:])
				sender = client
				whisper(sender, target, message)
			
			# LIST ALL CONNECTED USERS #
			elif cmd.decode('ascii').startswith('USERS'):
				client.send('Connected Users:'.encode('ascii'))
				for username in usernames:
					client.send(f'{username}'.encode('ascii'))
			
			# LIST ALL ACTIVE CHANNELS #
			elif cmd.decode('ascii').startswith('CHANNELS'):
				client.send('Active channels:'.encode('ascii'))
				with open('channel_list.txt', 'r') as c:
					valid_channels = c.readlines()
				tmp = ''.join(valid_channels)
				client.send(tmp.encode('ascii'))
				
			# JOIN A CHANNEL #
			elif cmd.decode('ascii').startswith('JOIN'):
				chanName = cmd.decode('ascii')[5:]
				if chanName.startswith('#'):
					join_channel(client, chanName)
				else:
					client.send('incorrect channel name format, use /help to display valid commands')
			
			# USER IS REQUESTING TO TRANSFER A FILE TO ANOTHER USER #
			elif cmd.decode('ascii').startswith('REQ'):
				content = (cmd.decode('ascii')[4:]).split
				c = content.split()
				target = c[0]
				filename = c[1]
				hostname = usernames[clients.index(client)]
				accepted = transfer_request(hostname, target, filename)
				if accepted:
					intermediate_file_acc(client)
					transfer_file(filename, target)
					rm_local(filename)
				else:
					client.send('FTP DENY')
					rm_local(filename)

			else:
				clientidx = clients(client)
				curChan = channel[clientidx]
				broadcast(message.encode('ascii'), curChan) #only executes if none of the command code above executes
		except:
			exit_seq(client)
			break		

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	bouncer_thread = threading.Thread(target = bouncer, daemon = True)
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
			
			print(f'The username of the client is {username}.')
			broadcast(f'{username} has joined the server.'.encode('ascii'), '#general')

			# we run one thread for each connected client because they all need to be handled simultaneously
			handle_thread = threading.Thread(target=handle, args=(client,))
			handle_thread.start()
		except:
			print('There was an error recieving client data')

receive()