""" 
Mohammad Rifat Arefin
ID: 1001877262  
"""
import socket
import threading
import re
import tkinter as tk
import os
import pickle
import time

""" create a TCP socket """
backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       #socket for requests from primary server
backup_socket.bind(('localhost',12102))    #create server on a port
backup_socket.listen()

server_port = 12101
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost',server_port))    #create server on a port
server_socket.listen()                          
print ('The server is ready to receive')

poll_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #create socket for polling clients
poll_socket.bind(('localhost',12106))    #create server on a port
poll_socket.listen()
lexicon = set()                                #read lexicon from file
client_name = set()                            #currently connected clients
name2 = set(client_name)                       #for checking arriving or leaving clients

server = 0                                      #check if primary joined or not

""" thread for each client """
def listen(connection_socket, username):

    while(True):
        try:
            header = connection_socket.recv(1024).decode()        #check header for data or polling req
            if (header =="data"):
                connection_socket.send("send data".encode())        #send ack
                
                break
            elif (len(header) == 0):                                #break if client disconnect 
                break
            elif (header == "lexicon"):
                print("header lexicon")
                connection_socket.send("send_lexicon".encode())     #send ack
                lex = connection_socket.recv(1024)                  #recv lexicon
                lex = pickle.loads(lex)
                global lexicon
                lexicon = lexicon.union(lex)
                print(lexicon)
        except Exception as e:
            print(e)
            print("prob")
            continue

    
    data = b''
    while(True):                                #receive file in chunks
        chunk = connection_socket.recv(1024)
        data += chunk
        if len(chunk)<1024:
            break


    print(data.decode()+username)
    st = data.decode()                          #convert binary to text
    for i in lexicon:                           #replace misspelled words
        word = r'\b' +i +r'\b'
        pattern = re.compile(word,re.IGNORECASE)
        for m in re.findall(pattern, st):

            st = st.replace(m,'['+m+']')
    connection_socket.send(st.encode())         #send checked file
        
    connection_socket.close()                   #close socket
    client_name.remove(username)                #remove from list


""" refresh client names real time
master -> frame to refresh """
def real_time(master, client_label):
    if server == 1:
        client_label['text'] = "Server connected\n"
    else:
        client_label['text'] = "Server not connected\n"
    client_label['text'] += str(len(client_name))+" client(s) connected\n"+ str([x for x in client_name])+"\n"
    global name2                                    #compare with older client names
    if(len(client_name)<len(name2)):                #check leaving clients
        client_label['text']+=str(name2.difference(client_name)) +" has left"
    elif(len(client_name)>len(name2)):              #check arriving clients
        client_label['text']+=str(client_name.difference(name2)) +" has arrived"
    name2 = set(client_name)
    master.after(3000, real_time, master, client_label)#calls itself every 3 secs

""" thread for real time GUI """
def show_clients():
    master = tk.Tk()                                            # draw server window
    master.title("Backup Server")
    master.geometry("500x200")
    # tk.Label(master, text="Server started").grid()
    client_label = tk.Label(master, text=[x for x in client_name])
    client_label.grid()
    tk.Button(master, text = "Quit",command=lambda: quit_app(master)).grid()
    real_time(master, client_label)                            #refresh client names real time
    tk.mainloop()
    server_socket.close()
    os._exit(1)

""" thread for polling """
def polling(poll):                                                  
    # print("addr")
    while(1):
        
        try:
                 #send polling req
            time.sleep(10)
            print("sending")
            poll.send("polling".encode())               #send polling req to each client
        except:
            break
                
    
""" Quit button action """
def quit_app(master):
    master.destroy()
    server_socket.close()
    os._exit(1)

""" thread for checking requsts from primary server """
def server_join():
    while(1):
        back_conn, badd = backup_socket.accept()            #accept connection from primary server
        global server
        server = 1
        print(back_conn.recv(1024).decode())                #recv ack
        while(1):
            try:
                back_conn.send("send lex".encode())
                lex = back_conn.recv(1024)                  #recv lexicon
                lex = pickle.loads(lex)
                global lexicon
                lexicon = lexicon.union(lex)
                print(lexicon)
            except:
                server = 0
                break

threading.Thread(target=show_clients).start()       #start thread for real time GUI
threading.Thread(target=server_join).start()            #start thread for polling

while 1: 
    
    connection_socket, addr = server_socket.accept()        #accept new clients
    username = connection_socket.recv(1024).decode()        #receive username
    if username not in client_name and len(client_name)<3:  #send ok msg if no conflict
        client_name.add(username)
        
        connection_socket.send("ok".encode())
        poll, p_addr = poll_socket.accept()                 #connection for polling clients

        print(poll.recv(1024).decode())
        threading.Thread(target=polling, args= (poll,)).start()            #start thread for polling
    
    else:                                                   #reject with a msg
        if username in client_name:
            connection_socket.send("duplicate".encode())
        else:
            connection_socket.send("full_capacity".encode())

        connection_socket.close()
        continue

    # new threads will be forked for each connected client
    threading.Thread(target=listen, args= (connection_socket, username)).start()
