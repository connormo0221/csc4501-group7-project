import threading
import socket
#import os
import sys

# TODO: make sure the client will exit by itself upon most errors

# Allow client to set their username; used for display on the server
username = input('Type in a username: ')
if username == 'admin':
	password = input('Type in a password: ')

# Server host IP & port number manually set to localhost for this project
host = '127.0.0.1'
port = 29170

# Open new socket and connect using host IP and port number defined above
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, int(port)))

stop_thread = False
fname = ''
hname = ''

# Add client commands to the help message here
help_msg = 'Valid commands:\n/help, /exit, /w [user] [message], /online, /channels, /join #[channel name], /transfer [user] [path to file]'
# Add admin commands to the help message here
admin_help_msg = 'Additional commands for admins:\n/kick [user], /ban [user], /unban [user], /make #[channel name], /close #[channel name]'

# function Receive
# Receives & decodes data from the server; if data can't be decoded, client disconnects
def receive():
	while True:
		global stop_thread
		global hname
		global fname
		# Use the following line for debugging thread closure
		#print(f'DEBUG_CLIENT: stop_thread == {stop_thread}')
		if stop_thread == True:
			# Use the following line for debugging thread closure
			#print('DEBUG_CLIENT: Breaking receive() loop.')
			client.close()
			print('All connections closed.')
			break

		try:
			message = client.recv(1024).decode('ascii') # Server uses a client to send messages
			if message == 'ID':
				client.send(username.encode('ascii'))
				next_msg = client.recv(1024).decode('ascii')
				if next_msg == 'PASS': # Using PASS keyword to ask for password
					client.send(password.encode('ascii'))
					if client.recv(1024).decode('ascii') == 'REFUSE':
						print('ERROR: Connection refused due to invalid password.')
						stop_thread = True
				elif next_msg == 'BAN': # Using BAN keyword to disconnect user
					print('ERROR: Connection refused due to being banned by an administrator.')
					stop_thread = True
			elif message == 'KICKED': # Using KICKED keyword to disconnect user
				print('ERROR: Connection refused; user was kicked from the server by an administrator.')
				stop_thread = True
			elif message == 'EXIT': # Using EXIT keyword to disconnect user
				stop_thread = True
			elif message.startswith('FTP_REQ'): # Using FTP_REQ keyword to request file transfer
				content = message.split()
				hname = content[1]
				fname = content[2]
				print(f'{content[1]} would like to transfer file {content[2]}. Will you accept? Type /accept or /deny')
			elif message.startswith('FTP_CONF'): # Indicates a positive response from another client to a FTP_REQ
				file = message[9:]
				f = open(file, 'rb')
				#f_size = os.path.getsize(file) # Uncomment this if we want to implement a progress bar
				#client.send(str(f_size).encode()) # Uncomment this if we want to implement a progress bar
				data = f.read()
				client.sendall(data)
				client.send(b"<END>")
				f.close()
			elif message.startswith('DATA_RECV'): # Indicates that a file is being transferred
				filename = client.recv(1024).decode()
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
				file_bytes = file_bytes[:-5] # Remove bytes containing <END> message 
				file.write(file_bytes)
				file.close()
				print(f'{filename} has been transferred successfully!')

			else:
				print(message)
		
		except IOError:
			print('Data transfer stopped, closing connection.')
			client.close() # Close socket connected to the server
			break
	
	# This line is only reached if the receive() loop has been broken
	print('Press ENTER to exit.') # Force the user to move control out of the write() thread below

# function Write
# Waits for user input & then sends a message to the server upon pressing the enter key
def write():
	global stop_thread
	global fname
	global hname
	while True: # Always running in order to catch input
		try:
			content = input("")
			isAdmin = False
			if username == 'admin': # Change this if we decide to add support for multiple admins
				isAdmin = True

			if content.startswith('/'): # Forward slash indicates a command is being used; check which command
				if (content.startswith('/help')):
					print(help_msg)
					if isAdmin:
						print(admin_help_msg)
				
				elif (content.startswith('/kick') & isAdmin): # Kicks a user temporarily
					print(f'Kicking user {content[6:]}.')
					client.send(f'KICK {content[6:]}'.encode('ascii'))

				elif (content.startswith('/ban') & isAdmin): # Bans a user
					print(f'Banning user {content[5:]}.')
					client.send(f'BAN {content[5:]}'.encode('ascii'))

				elif (content.startswith('/unban') & isAdmin): # Unbans a user
					print(f'Unbanning user {content[7:]}.')
					client.send(f'UNBAN {content[7:]}'.encode('ascii'))

				elif (content.startswith('/make') & isAdmin): # Make a new server channel
					client.send(f'MAKE {content[6:]}'.encode('ascii'))

				elif (content.startswith('/close') & isAdmin): # Closes an existing server channel
					client.send(f'CLOSE {content[7:]}'.encode('ascii'))

				elif (content.startswith('/exit')): # Exits the server
					print('Now exiting the server.')
					client.send('EXIT'.encode('ascii'))
				
				elif (content.startswith('/w')): # Sends a private message to another user
					print('Whispering to another user.')
					client.send(f'WHISPER {content[3:]}'.encode('ascii'))

				elif (content.startswith('/online')): # Lists all users that are currently online
					client.send('USERS'.encode('ascii'))

				elif (content.startswith('/channels')): # Lists all available server channels
					client.send('CHANNELS'.encode('ascii'))

				elif (content.startswith('/join')): # Moves user to another server channel
					client.send(f'JOIN {content[6:]}'.encode('ascii'))
				
				elif (content.startswith('/transfer')): # Sends a request for file transfer to another user
					command = content.split()
					target = command[1]
					file = command[2]
					client.send(f'REQ {target} {file}'.encode('ascii'))
					print('Press ENTER to confirm.') # Force user to move control to the receive() thread
					continue
				
				elif(content.startswith('/accept')):
					client.send(f'FTP_AFF {hname} {fname}'.encode('ascii'))
					hname = ''
					fname = ''

				elif(content.startswith('/deny')):
					client.send(f'FTP_NEG {hname} {fname}'.encode('ascii'))
					hname = ''
					fname = ''

				else:
					print('ERROR: Invalid command. Use /help to list all valid commands.')
			else:
				message = (f'{username}: {content}')
				client.send(message.encode('ascii'))

		except IOError:
			if receive_thread.is_alive(): # Only send error message if receive() thread is still active
				stop_thread = True # Tell receive() thread to stop
				print('ERROR: Unable to send a message to the server.')
			break
	# Use the following line for debugging thread closure
	#print('DEBUG_CLIENT: Broke write() loop successfully.')
		
# Both functions need their own thread since we need to be able to send & receive messages simultaneously
receive_thread = threading.Thread(target = receive)
receive_thread.start()

write_thread = threading.Thread(target = write)
write_thread.start()

if (not receive_thread.is_alive()) & (not write_thread.is_alive()):
	sys.exit() # Exit client if both threads have been closed