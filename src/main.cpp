#include <iostream>
#include <WS2tcpip.h>

#pragma comment (lib, "ws2_32.lib")


int main() 
{
    //initialize winsock
    WSADATA wsData;
    WORD ver = MAKEWORD(2, 2);

    int wsOk = WSAStartup(ver, &wsData);
    if (wsOk != 0)
    {
        std::cerr << "Cannot initialize winsock, quitting." << std::endl;
        return 1; 
    }

    //create a socket 
    SOCKET listening = socket(AF_INET, SOCK_STREAM, 0);
    if (listening == INVALID_SOCKET)
    {
        std::cerr << "cannot create a socket, quitting." << std::endl;
        return 1;
    }

    //bind an ip address and port (this is the server ip and port) to the socket
    sockaddr_in hint;
    hint.sin_family = AF_INET;
    hint.sin_port = htons (54000); /* networking is big ending while pcs are little endian which is why this is here */
    hint.sin_addr.S_un.S_addr = INADDR_ANY; /* could use inet_pton, whatever that is*/

    bind(listening, (sockaddr*)&hint, sizeof(hint));

    //tell winsock the socket is for listening
    listen(listening, SOMAXCONN); /*just marks the socket for listening, but doesnt actually listen*/

    //wait for a connection
    sockaddr_in client;
    int clientSize = sizeof(client);

    SOCKET clientSocket = accept(listening, (sockaddr*)&client, &clientSize);
    if (clientSocket == INVALID_SOCKET)
    {
        std::cerr << "cannot create a socket, quitting." << std::endl;
        return 1;
    }

    char host[NI_MAXHOST]; //client's remot name
    char service[NI_MAXHOST]; //service Iport) the client is connected to

    ZeroMemory(host, NI_MAXHOST);
    ZeroMemory(service, NI_MAXHOST);

    if(getnameinfo((sockaddr*)&client, sizeof(client), host, NI_MAXHOST, service, NI_MAXSERV, 0) == 0)
    {
        std::cout << host << " connected on port " << service << std::endl;
    }
    else
    {
        inet_ntop(AF_INET, &client.sin_addr, host, NI_MAXHOST);
        std::cout << host << " connected on port " << ntohs(client.sin_port) << std::endl;
    }

    //close listening socket
    closesocket(listening);

    //while loop: accept and echo message back to client
    char buf [4096];
    while (true)
    {
        ZeroMemory(buf, 4096);

        //wait for client to send data
        int bytesRecieved = recv(clientSocket, buf, 4096, 0);
        if (bytesRecieved == SOCKET_ERROR)
        {
            std::cerr << "Error in recv(). Quitting" << std::endl;
            break;
        }
        if (bytesRecieved == 0)
        {
            std::cout << "client disconnected" << std::endl;
            break;
        }

        //echo message back to the client
        send(clientSocket, buf, bytesRecieved+1, 0); //bytesRecieved has a 1 added because it appends a zero

    }

    //close the socket
    closesocket(clientSocket);

    //cleanup winsock
    WSACleanup();

    return 0;
}