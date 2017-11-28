from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import gather_configs as GC

class MainWindow(Frame):
    
    def __init__(self,parent):
        parent.title("glspi's Gather Configs")
        parent.geometry("450x300")
        ttk.Frame.__init__(self,parent)
        self.devicelist = StringVar()
        self.configpath = StringVar()
    
        self.devicelist_label = ttk.Label(text="Choose device list: ", font=(None,14))
        self.devicelist_label.grid(row = 0, column = 0, sticky = W)
        self.devicelist_Text = Text(width = 45, height = 2, wrap = WORD, relief = SUNKEN)
        self.devicelist_Text.grid(row=1,column=0,sticky = W)
        self.devicelist_Text.bind('<Tab>',self.focus_next_box)
        self.button1 = Button(text="...", command=self.pickfile)
        self.button1.grid(row=1,column=1,padx=10,sticky=W)
        
        self.configpath_label = ttk.Label(text="Choose output config path: ", font=(None,14))
        self.configpath_label.grid(row = 3, column = 0, sticky = W)
        self.configpath_Text = Text(width = 45, height = 2, wrap = WORD, relief = SUNKEN)
        self.configpath_Text.grid(row=4,column=0,sticky = W)
        self.configpath_Text.bind('<Tab>',self.focus_next_box)
        self.button2 = Button(text="...", command=self.pickoutput)
        self.button2.grid(row=4,column=1,padx=10,sticky=W)
        
        self.username_label = ttk.Label(text="Username: ", font=(None,12))
        self.username_label.grid(row = 6, column = 0, sticky = W,pady=10)
        self.username_Text = ttk.Entry(width = 35)
        self.username_Text.bind('<Tab>',self.focus_next_box)
        self.username_Text.grid(row=7,column=0,sticky = W)
        
        self.password_label = ttk.Label(text="Password: ", font=(None,12))
        self.password_label.grid(row = 8, column = 0, sticky = W)
        self.password_Text = ttk.Entry(width = 35,show="*")
        self.password_Text.bind('<Tab>',self.focus_next_box)
        self.password_Text.grid(row=9,column=0,sticky = W)
        
        self.showpass = BooleanVar()
        self.password_showpass = ttk.Checkbutton(text="Show Password",variable=self.showpass,command=self.show_password)
        self.password_showpass.grid(row=9,column=1)
       
        self.start_button = ttk.Button(text="Gather Configs", command=self.start_gather)
        self.start_button.grid(row=15,column=0,pady=30) 

    def pickfile(self):
        self.devicelist_Text.delete(0.0,END)
        self.devicelist = filedialog.askopenfilename()
        self.devicelist_Text.insert(0.0,self.devicelist)
       
    def pickoutput(self):
        self.configpath_Text.delete(0.0,END)
        self.configpath = filedialog.askdirectory()
        self.configpath_Text.insert(0.0,self.configpath)
    
    def gather_configs(self):
        messagebox.showinfo("Title Test","Gathering Configs!")
        print("test")
    
    def focus_next_box(self,event):
        event.widget.tk_focusNext().focus()
        return("break")
        
    def show_password(self):
        if self.showpass.get():
            self.password_Text.config(show="")
        else:
            self.password_Text.config(show="*")
        
    def start_gather(self):
        username = self.username_Text.get()
        password = self.password_Text.get()
        GC.gather_configs(self.devicelist,self.configpath,username,password)
