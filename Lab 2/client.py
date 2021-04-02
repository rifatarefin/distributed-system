""" 
Mohammad Rifat Arefin
ID: 1001877262  
"""
import tkinter as tk
import socket
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfile

server_port = 12100
client_socket = None

""" Prompt user to choose file to send """
def open_file(root):
    path = open(askopenfilename(),'rb')                 #file chooser 
    client_socket.sendfile(path)
    

    root.grid_remove()

    root = tk.Frame(master, width=500, height=200)
    root.grid()


    get = client_socket.recv(1024).decode()
    print(get)
    
    
    tk.Label(root, text="Upload complete").grid()
    tk.Button(root, text = "Save as",command=lambda: save_file(root,get)).grid()
    root.tkraise()

""" Prompt user for destination location of spell checked file """
def save_file(root, data):

    file = asksaveasfile()              #destination location
    file.write(data)
    file.close()
    root.grid_remove() 
    root = tk.Frame(master, width=500, height=200)
    root.grid()
    tk.Label(root,text="Spell checking complete").grid()
    tk.Label(root,text="Successfully saved").grid()
    tk.Button(root, text = "Quit",command=lambda: quit_app()).grid()
    tk.Button(root, text = "Start over", command=lambda: restart(root)).grid()
    root.tkraise()

""" connect with the server and register a username """
def send_username(root_frame, entry):
    username = entry.get()
    print("username: %s" % (username))
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #create socket
    try:
        client_socket.connect(('localhost', server_port))               #connect with server
        client_socket.send(username.encode())
        
        root_frame.grid_remove()

        msg = client_socket.recv(1024).decode()               #receive server status

        frame2 = tk.Frame(master)
        frame2.grid()

        if(msg == "ok"):                          #servers sends ok if name available
            tk.Label(frame2, text="Welcome "+username).grid()
            tk.Button(frame2, text="Choose file", command=lambda:open_file(frame2)).grid()
            tk.Button(frame2, text = "Quit",command=quit_app).grid()
            frame2.tkraise()
        
        else:                                      #server rejects if name not available
            if(msg == "duplicate"):
                tk.Label(frame2, text="Name not available").grid()
                
            elif(msg == "full_capacity"):           #server rejects if already 3 clients running
                tk.Label(frame2, text="Already 3 clients running").grid()

            tk.Button(frame2, text = "Quit",command=quit_app).grid()
            tk.Button(frame2, text = "Retry", command=lambda: restart(frame2)).grid()
            frame2.tkraise()
    except:                                     #Notify username if server not connected
        root_frame.grid_remove()
        frame2 = tk.Frame(master)
        frame2.grid()
        tk.Label(frame2, text="Server not connected").grid()
        tk.Button(frame2, text="Quit", command=quit_app).grid()
        tk.Button(frame2, text = "Retry", command=lambda: restart(frame2)).grid()
        
""" restart client """        
def restart(root):
    root.grid_remove()
    client_socket.close()
    landing()

""" quit application """
def quit_app():
    master.destroy()
    client_socket.close()
    exit()

"""Prompt user for username  """
def landing():
    
    root_frame = tk.Frame(master, width=300, height=100)
    root_frame.grid()
    tk.Label(root_frame, text="Username").grid(row=0, column=0)
    entry = tk.Entry(root_frame, bd=5)
    entry.grid(row=0, column=1)
    tk.Button(root_frame, text="confirm",
            command=lambda: send_username(root_frame, entry)).grid(row=1)

    


master = tk.Tk()                    # draw client window
master.title("client")
master.geometry("500x200")
landing()                           #prompt for username
tk.mainloop()

client_socket.close()
