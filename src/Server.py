import threading
import socket

# localhost, change for a webserver
host = '127.0.0.1' 
#don't user reserved ports 1-10,000
port = 31103 

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
#puts the server into listening mode
server.listen() 
print('Server Online')

clients = []	#these two match up
usernames = []


#Broadcast Method
#sends a message to all currently connected clients

def broadcast(message):
	for client in clients:
		client.send(message)


#Client Connection Handling Method
#When a client connects to the server, recieve any messages and send them to all other clients including itself

def handle(client):
	while True:
		try:
			#sets message to a recieved message, up to 1024 bytes
			message = client.recv(1024)
			broadcast(message)
		except:
			index = clients.index(client)
			clients.remove(client)
			client.close()
			username = usernames[index]
			usernames.remove(username)
			broadcast(f'{username} has left the chat'.encode('ascii'))
			break


#Receive / Main method
#combines all other methods into one function

def receive():
	while True:
		#constantly running the accept method and if it finds anything it returns a client and address
		client, address = server.accept() 
		print(f"User has connected with IP and port {str(address)}")
		
		client.send('ID'.encode('ascii'))
		username = client.recv(1024).decode('ascii')
		usernames.append(username)
		clients.append(client)
		
		print(f'The username of the client is {username}!')
		broadcast(f'{username} has joined the server'.encode('ascii'))
		client.send('You have connected to the server succesfully'.encode('ascii'))
		
		#we run one thread for each connected client because they all need to be handled simultaneously
		thread = threading.Thread(target=handle, args=(client,))
		thread.start()

receive()