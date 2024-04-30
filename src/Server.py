import socket
import threading
import sys

host = '127.0.0.1' 
port = 29170 

server =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen() 


clients = [] 
usernames = [] 



def broadcast(message):
    for client in clients:
        client.send(message)
        
def isAdmin(client):
	if usernames[clients.index(client)] == 'admin':
		return True
	else:
		return False

#handle
def handle(client):
    
    while True:
        stop_thread = False
        if stop_thread == True:
            print("DEBUG_SERVER: Breaking handle() loop.")
            break
        try:
            cmd = message = client.recv(1024)
            broadcast(message)           
        except:
            print('ERROR: Exception in handle() loop, printing to terminal:')

#receive
def receive():
    
    while True:
        try:
            client, address = server.accept()
            print(f'User has connected with IP and port {str(address)}.')
            client.send('USER'.encode('utf-8'))
            username = client.recv(1024).decode('utf-8')
            
            if username == 'admin':
                client.send('PASS'.encode('utf-8'))
                password = client.recv(1024).decode('utf-8')
                if password != 'Bou-Harb':
                    print(f'User at {str(address)} attempted to login as administrator unsucessfully.')
                    client.send('REFUSE'.encode('utf-8'))
                    client.close()
                    continue
            
            '''
            with open('banslist.txt', 'r') as f:
                bans = f.readlines()
            
            if username + '\n' in bans:
                client.send('BAN'.encode('utf-8'))
                client.close()
                continue
            '''
            
            usernames.append(username)
            clients.append(client)

            client.send("Connected to the server\n".encode('utf-8'))
            print(f'The username of the client is {username}.')

            thread = threading.Thread(target=handle, args=(client,))  #comma to make this a tuple 
            thread.start()
        except:
            print('ERROR: Failed to receive client data.')
            break
print("Server running...")
receive()