import threading
import socket
import os
import sys

# TODO: find a way to incorporate the admin password w/o storing it as plaintext
# TODO: add method that automatically closes the window if the server is closed

host = '127.0.0.1' # localhost 
port = 29170 # Make sure to use an unassigned port number, best range is 29170 to 29998 [main req is port # > 10,000]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() # Puts the server into listening mode
print(f'Server is now online. Awaiting connections on {host}/{port}.')

# Storing connected client info into lists; a single index value should correspond to a user in all lists
clients = [] # stores (host, port) pairs
usernames = [] # stores client usernames
channel = [] # stores the name of the user's current channel

# Default communication method
# Sends a message to all clients in the same channel as the sender
def broadcast(message, sender_channel):
	for client in clients:
		client_index = clients.index(client)
		if channel[client_index] == sender_channel:
			client.send(message)

# Checks if a client has administrator privileges
def isAdmin(client):
	if usernames[clients.index(client)] == 'admin':
		return True
	else:
		return False

# Kicks a user from the server
def kick_user(name):
	client_index = usernames.index(name)
	client = clients[client_index]
	curr_channel = channel[client_index]
	del clients[client_index]
	del usernames[client_index]
	del channel[client_index]
	client.send('KICKED'.encode('ascii')) # Send KICKED keyword to client to stop their receive() thread
	broadcast(f'{name} has been kicked by an admin.'.encode('ascii'), curr_channel)

# Kicks a user from the server and then adds their name to the banlist
def ban_user(to_be_banned, client):
	tmp = to_be_banned + '\n' # Add newline character; needed for the file check to work
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if tmp in banned_users:
		client.send('ERROR: This user has already been banned.'.encode('ascii'))
	else:
		kick_user(to_be_banned)
		with open('banlist.txt', 'a') as a: # Storing in a text file for continuity
			a.write(f'{to_be_banned}\n')

# Removes a username from the banlist, if present
def unban_user(to_be_unbanned, client):
	to_be_unbanned = to_be_unbanned + '\n' # Add newline character; needed for the file check to work
	with open('banlist.txt', 'r') as r:
		banned_users = r.readlines()
	if to_be_unbanned in banned_users:
		with open('banlist.txt', 'w') as w:
			for line in banned_users:
				if line != to_be_unbanned:
					w.write(line)
	else:
		client.send('ERROR: This user has not been banned.'.encode('ascii'))

# Creates a new text channel
def create_channel(channel_name, client):
	channel_name = channel_name + '\n' # Add newline character; needed for the file check to work
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()
	if channel_name in valid_channels:
		client.send('ERROR: Channel already exists.'.encode('ascii'))
	else:
		with open('channel_list.txt', 'a') as f: # Storing in a text file for continuity
			f.write(f'{channel_name}')

# Closes a text channel by moving all users to general and then removing it from the channel list
def close_channel(channel_name, client):
	channel_name = channel_name + '\n' # Add newline character; needed for the file check to work
	with open('channel_list.txt', 'r') as r:
		valid_channels = r.readlines()
	if channel_name in valid_channels:
		for c in channel:
			if c == channel_name:
				clients[channel.index(c)].send('An admin has closed the channel you were in. You will be moved to #general.'.encode('ascii'))
				join_channel(clients[channel.index(c)], '#general')
		with open('channel_list.txt', 'w') as w: # Re-writes the channel_list file (Python workaround)
			for line in valid_channels:
				if line != channel_name:
					w.write(line)
	else:
		client.send('ERROR: Cannot remove a channel that does not exist.'.encode('ascii'))

# Method for exiting the server; by default, sends EXIT keyword to the client
def exit_seq(client, still_connected = True):
	client_index = clients.index(client) # Get a client's index via their (host, port) pair
	name = usernames[client_index] # Use index to get client name for broadcast
	curr_channel = channel[client_index] # Use index to get current channel for broadcast
	del clients[client_index]
	del usernames[client_index]
	del channel[client_index]
	broadcast(f'{name} has left the server.'.encode('ascii'), curr_channel)
	if still_connected == True:
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
	channel_name = channel_name + '\n' # Add newline character; needed for the file check to work
	with open('channel_list.txt', 'r') as c:
		valid_channels = c.readlines()
	if channel_name in valid_channels:
		client_index = clients.index(client)
		username = usernames[client_index]
		channel[client_index] = channel_name
		broadcast(f'{username} has joined {channel_name[:-1]}!'.encode('ascii'), channel_name)
		client.send(f'You have joined {channel_name[:-1]} succesfully.'.encode('ascii'))
	else:
		client.send('ERROR: Channel does not exist.'.encode('ascii'))

# Send request for file transfer to another client
def transfer_request(hostname, clientname, filename):
	client = clients[usernames.index(clientname)]
	client.send(f'FTP_REQ {hostname} {filename}'.encode('ascii'))

# Receive a file from the sender's computer
def intermediate_file_acc(client, filename):
	client.send(f'FTP_CONF {filename}'.encode('ascii'))
	#file_size = client.recv(1024).decode() # Uncomment this if we want to implement a progress bar
	file = open(filename, 'wb')
	file_bytes = b""
	done = False
	while not done:
		data = client.recv(1024)
		if file_bytes[-5:] == b"<END>":
			done = True
		else:
			file_bytes += data
	file_bytes = file_bytes[:-5] # Remove bytes containing <END> message from the file
	file.write(file_bytes)
	file.close()

# Send a file from the host computer
def transfer_file(filename, target):
	f = open(filename, 'rb')
	#f_size = os.path.getsize(filename) # Uncomment this if we want to implement a progress bar
	target.send('DATA_RECV'.encode('ascii'))
	target.send(filename.encode())
	#target.send(str(f_size).encode()) # Uncomment this if we want to implement a progress bar
	data = f.read()
	target.sendall(data)
	target.send(b"<END>")
	f.close()

# Remove a file from the host computer
def rm_local(filename):
	if os.path.exists(filename):
		os.remove(filename)
	else:
		print(f'ERROR: File deletion was attempted on filename {filename} but no such file exists.')

# function Client Connection Handler
# When a client connects to the server, receive messages from client & send them to all clients (including itself)
def handle(client):
	while True:
		stop_thread = False
		if stop_thread == True:
			# Use the following line for debugging thread closure
			#print('DEBUG_SERVER: Breaking handle() loop.')
			break
			
		try:
			# Sets message to a received message, up to 1024 bytes
			cmd = message = client.recv(1024)
   
			# Check using keywords if a message is a command
			## ADMIN COMMANDS ##
			if cmd.decode('ascii').startswith('KICK'): # KICKS A USER FROM THE SERVER
				if isAdmin(client):
					kicked_user = cmd.decode('ascii')[5:]
					if kicked_user in usernames:
						kick_user(kicked_user)
					else:
						client.send(f'ERROR: No user by the name of {kicked_user} exists.'.encode('ascii'))
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
					new_channel = cmd.decode('ascii')[6:]
					if new_channel == '#general':
						client.send('ERROR: Cannot remove the default channel.'.encode('ascii'))
					elif new_channel.startswith('#'):
						close_channel(new_channel, client)
					else:
						client.send('ERROR: Invalid channel name format, use /help to display valid commands.'.encode('ascii'))
				else:
					client.send('ERROR: Command refused.'.encode('ascii'))

			## CLIENT COMMANDS ##
			elif cmd.decode('ascii') == ('EXIT'): # EXITS THE SERVER
				exit_seq(client)
				stop_thread = True
				break

			elif cmd.decode('ascii').startswith('WHISPER'): # MESSAGE A SPECIFIC PERSON
				content = (cmd.decode('ascii')[8:]).split()
				target = content[0]
				message = (content[1:])
				sender = client
				whisper(sender, target, message)
			
			elif cmd.decode('ascii').startswith('USERS'): # LIST ALL CONNECTED USERS
				client.send('Connected users:'.encode('ascii'))
				for username in usernames:
					client.send(f'{username}'.encode('ascii'))
			
			elif cmd.decode('ascii').startswith('CHANNELS'): # LIST ALL ACTIVE CHANNELS
				client.send('Active channels:'.encode('ascii'))
				with open('channel_list.txt', 'r') as c:
					valid_channels = c.readlines()
				tmp = ''.join(valid_channels)
				client.send(tmp.encode('ascii'))
				
			elif cmd.decode('ascii').startswith('JOIN'): # JOIN A NEW CHANNEL
				channel_name = cmd.decode('ascii')[5:]
				if channel_name.startswith('#'):
					join_channel(client, channel_name)
				else:
					client.send('ERROR: Incorrect channel name format, use /help to display valid commands.'.encode('ascii'))
					
			elif cmd.decode('ascii').startswith('REQ'): # REQUEST FILE TRANSFER TO ANOTHER USER
				content = cmd.decode('ascii')[4:]
				c = content.split()
				targetname = c[0]
				filename = c[1]
				hostname = usernames[clients.index(client)]
				intermediate_file_acc(client, filename)	# Temporarily stores file on server
				transfer_request(hostname, targetname, filename)
				print(f'File transfer request made to {targetname} by {hostname}.\nFile {filename} stored in temporary storage.')

			elif cmd.decode('ascii').startswith('FTP_AFF'): # TARGET USER ACCEPTED FILE TRANSFER
				content = cmd.decode('ascii').split()
				hostname = content[1]
				filename = content[2]
				host = clients[usernames.index(hostname)]
				host.send('User has accepted your file transfer request.'.encode('ascii'))
				transfer_file(filename, client)
				rm_local(filename) # Deletes the server's local copy of the file
				host.send(f'{filename} has been transferred successfully!'.encode('ascii'))
				print(f'User has accepted file transfer.\nFile {filename} deleted from temporary storage.')
			
			elif cmd.decode('ascii').startswith('FTP_NEG'): # TARGET USER DENIED FILE TRANSFER
				content = cmd.decode('ascii').split()
				hostname = content[1]
				filename = content[2]
				host = clients[usernames.index(hostname)]
				host.send('User has denied your file transfer request.'.encode('ascii'))
				rm_local(filename) # Deletes the server's local copy of the file
				print(f'User has denied file transfer.\nFile {filename} deleted from temporary storage.')

			else: # Only executes if no commands were used
				if client in clients:
					client_index = clients.index(client)
					curr_channel = channel[client_index]
					broadcast(message, curr_channel)
				else: # Used for when a client's data has been erased
					stop_thread = True
					break 
		
		# For connection errors
		except ConnectionError as err_con:
			print(f'ERROR: Exception {type(err_con).__name__} thrown within handle() loop, printing details to terminal:')
			print(sys.exception()) # Print exception to the terminal w/o closing the server
			exit_seq(client, False) # Start client exit sequence w/o sending an EXIT message
			break
		# For file I/O errors
		except (EOFError, UnicodeError, FileExistsError, FileNotFoundError, IsADirectoryError, NotADirectoryError, PermissionError) as err_io:
			print(f'ERROR: Exception {type(err_io).__name__} thrown within handle() loop, printing details to terminal:')
			print(sys.exception()) # Print exception to the terminal w/o closing the server
			exit_seq(client) # Start client exit sequence
			break
	# Use the following line for debugging thread closure
	#print('DEBUG_SERVER: Broke handle() loop successfully.')

# function Receive
# Combines all other methods into one function; used for receiving data from the client
def receive():
	while True:
		try:
			# Always running the accept method; if it finds something, return client & address
			client, address = server.accept() 
			print(f'User has connected with IP and port {str(address)}.')
			client.send('ID'.encode('ascii'))
			username = client.recv(1024).decode('ascii')

			with open('banlist.txt', 'r') as f:
				bans = f.readlines()
			
			if username + '\n' in bans:
				client.send('BAN'.encode('ascii'))
				client.close()
				continue

			# Checking if the user is attempting to login as an administrator
			if username == 'admin': # Change this if we decide to add support for multiple admins
				client.send('PASS'.encode('ascii')) # Indicates we want the client to send their password
				password = client.recv(1024).decode('ascii') # Assuming the client sends a password back we need to check it
				if password != 'Bou-Harb':
					print(f'User at {str(address)} attempted to login as administrator unsuccesfully.')
					client.send('REFUSE'.encode('ascii'))
					client.close()
					continue # The while-true loop needs to continue, but the code below shouldn't execute for an incorrect login

			usernames.append(username)
			clients.append(client)
			channel.append('#general\n') # Users are put in #general chat by default upon joining
			
			print(f'The username of the client is {username}.')
			broadcast(f'{username} has joined the server.'.encode('ascii'), '#general\n')

			# We run one thread for each connected client because they all need to be handled simultaneously
			handle_thread = threading.Thread(target = handle, args = (client,), daemon = True)
			handle_thread.start()

		except IOError:
			print('ERROR: Failed to receive client data.')
			break
	# Use the following line for debugging thread closure
	#print('DEBUG_SERVER: Broke receive() loop successfully.')

receive()
sys.exit() # Closes the server once no threads are left