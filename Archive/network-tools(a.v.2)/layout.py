from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import file_run_commands as FI
import apic_run_commands as AP

class MainWindow(Frame):
    
    def __init__(self,parent):
        parent.title("glspi's Gather Information")
        parent.geometry("900x700")
        ttk.Frame.__init__(self,parent)

        self.apic_or_file = StringVar(value="not selected")
        self.devicelist = StringVar()
        self.configpath = StringVar()
        self.showpass = BooleanVar()
        self.apicshowpass = BooleanVar()
        self.outputfolder = BooleanVar()

        self.pullfrom_label = ttk.Label(text="Pull devices from:", font=(None,14))
        self.pullfrom_label.grid(row = 0, column = 0, sticky = W)
        self.pullfromapic_button = Radiobutton(text="APIC-EM", variable=self.apic_or_file, value="apic-em", command=self.pullfrom_apic)
        self.pullfromapic_button.grid(row = 1, column = 0)
        self.pullfromapic_button.bind('<Tab>',self.focus_next_box)
        self.pullfromfile_button = Radiobutton(text="Device File", variable=self.apic_or_file, value="file", command=self.pullfrom_file)
        self.pullfromfile_button.grid(row=2, column=0)
        self.pullfromfile_button.bind('<Tab>',self.focus_next_box)
        self.spacer = ttk.Label()
        self.spacer.grid(row=3, column=3, pady=30)

        self.apic_label = ttk.Label(text="APIC-EM Credentials:", font=(None, 14))
        self.apicip_label = ttk.Label(text="\tIP Address")
        self.apicip_Text = ttk.Entry(width=35)
        self.apicuser_label = ttk.Label(text="\tUsername: ")
        self.apicuser_Text = ttk.Entry(width=35)
        self.apicuser_Text.bind('<Tab>', self.focus_next_box)
        self.apicpass_label = ttk.Label(text="\tPassword: ")
        self.apicpass_Text = ttk.Entry(width=35, show="*")
        self.apicpass_Text.bind('<Tab>', self.focus_next_box)

        self.apicpassword_showpass = ttk.Checkbutton(text="Show Password", variable=self.apicshowpass,
                                                 command=self.show_password_apic)

        self.devicelistapic_label = ttk.Label(text="Search APIC-EM based on device TAG:\n(leave blank to find all devices)")
        self.devicelistapic_Text = ttk.Entry(width = 35)
        self.devicelistapic_Text.bind('<Tab>',self.focus_next_box)

        self.devicelistfile_label = ttk.Label(text="Choose device list file (.yml): ", font=(None,14))
        self.devicelistfile_Text = Text(width=45, height=2, wrap=WORD, relief=SUNKEN)
        self.devicelistfile_Text.bind('<Tab>', self.focus_next_box)
        self.button1file = Button(text="...", command=self.pickfile)

        self.devicecredentials = ttk.Label(text="Network Device Credentials: ", font=(None,14))
        self.username_label = ttk.Label(text="\tUsername: ")
        self.username_Text = ttk.Entry(width=35)
        self.username_Text.bind('<Tab>', self.focus_next_box)

        self.password_label = ttk.Label(text="\tPassword: ")
        self.password_Text = ttk.Entry(width=35, show="*")
        self.password_Text.bind('<Tab>', self.focus_next_box)

        self.password_showpass = ttk.Checkbutton(text="Show Password", variable=self.showpass,
                                                 command=self.show_password)

        self.commands_label = ttk.Label(text="Command(s) to run on devices (one per line):", font=(None, 14))
        self.commands_Text = Text(width=60,height=5, borderwidth=2,relief=SUNKEN)
        self.commands_Text.bind('<Tab>', self.focus_next_box)

        self.outputfolderoption = ttk.Checkbutton(text="Log output to files?", variable=self.outputfolder,
                                                    command=self.outputfolderchecked)
        self.configpath_label = ttk.Label(text="Choose output log destination folder: ", font=(None, 14))
        self.configpath_Text = Text(width=45, height=2, wrap=WORD, relief=SUNKEN,border=1)
        
        self.configpath_label = ttk.Label(text="Choose output config path: ", font=(None, 14))
        self.configpath_Text = Text(width=45, height=2, wrap=WORD, relief=SUNKEN)
        self.configpath_Text.bind('<Tab>', self.focus_next_box)
        self.button2 = Button(text="...", command=self.pickoutput)

        self.start_button = ttk.Button(text="Push commands (START!)", command=self.start_gather)

        self.devicecredentials.grid(row=18,column=0,sticky=W)
        self.username_label.grid(row=19, column=0, sticky=W)
        self.username_Text.grid(row=19, column=1, sticky=W)
        self.password_label.grid(row=22, column=0, sticky=W)
        self.password_Text.grid(row=22, column=1, sticky=W)
        self.password_showpass.grid(row=22, column=2, sticky=E)
        self.commands_label.grid(row=24,column=0, sticky=W)
        self.commands_Text.grid(row=25,column=0, sticky=W)

        self.outputfolderoption.grid(row=28,column=1,sticky=W)
        #self.configpath_label.grid(row=27, column=0, sticky=W)
        #self.configpath_Text.grid(row=28, column=0, sticky=W)
        #self.button2.grid(row=28, column=1, padx=10, sticky=E)

        self.start_button.grid(row=35, column=0, pady=30)

    def pullfrom_apic(self):
        self.devicelistfile_label.grid_remove()
        self.devicelistfile_Text.grid_remove()
        self.button1file.grid_remove()

        self.apic_label.grid(row=4,column=0,sticky=W)
        self.apicip_label.grid(row=5,column=0,sticky=W)
        self.apicip_Text.grid(row=5,column=1,sticky=W)
        self.apicuser_label.grid(row=6,column=0,sticky=W)
        self.apicuser_Text.grid(row=6,column=1,sticky=W)
        self.apicpass_label.grid(row=7,column=0,sticky=W)
        self.apicpass_Text.grid(row=7,column=1,sticky=W)
        self.apicpassword_showpass.grid(row=7,column=2)
        self.devicelistapic_label.grid(row = 8, column = 0, sticky = W)
        self.devicelistapic_Text.grid(row=8,column=1,sticky = W, pady=30)

    def pullfrom_file(self):
        self.apic_label.grid_remove()
        self.apicip_label.grid_remove()
        self.apicip_Text.grid_remove()
        self.apicuser_label.grid_remove()
        self.apicuser_Text.grid_remove()
        self.apicpass_label.grid_remove()
        self.apicpass_Text.grid_remove()
        self.devicelistapic_label.grid_remove()
        self.devicelistapic_Text.grid_remove()
        self.apicpassword_showpass.grid_remove()

        self.devicelistfile_label.grid(row=4, column=0, sticky=W)
        self.devicelistfile_Text.grid(row=5, column=0, sticky=W)
        self.button1file.grid(row=5, column=1, padx=10, sticky=W,pady=30)

    def pickfile(self):
        self.devicelistfile_Text.delete(0.0, END)
        self.devicelist = filedialog.askopenfilename()
        self.devicelistfile_Text.insert(0.0, self.devicelist)

    def pickoutput(self):
        self.configpath_Text.delete(0.0, END)
        self.configpath = filedialog.askdirectory()
        self.configpath_Text.insert(0.0, self.configpath)

    def focus_next_box(self,event):
        event.widget.tk_focusNext().focus()
        return("break")

    def show_password(self):
        if self.showpass.get():
            self.password_Text.config(show="")
        else:
            self.password_Text.config(show="*")

    def show_password_apic(self):
        if self.apicshowpass.get():
            self.apicpass_Text.config(show="")
        else:
            self.apicpass_Text.config(show="*")
            
    def outputfolderchecked(self):
        if self.outputfolder.get():
            self.configpath_label.grid(row=30, column=0, sticky=W)
            self.configpath_Text.grid(row=31, column=0, sticky=W)
            self.button2.grid(row=32, column=0, padx=10, sticky=E)
        else:
            self.configpath_label.grid_remove()
            self.configpath_Text.grid_remove()
            self.button2.grid_remove()
            self.configpath_Text.delete(0.0, END)

    def start_gather(self):
        username = self.username_Text.get()
        password = self.password_Text.get()
        configpath = self.configpath_Text.get('1.0','end').strip('\n')
        commandlist = self.commands_Text.get('1.0', 'end').splitlines()

        if self.outputfolder.get():
            if configpath == '':
                messagebox.showinfo('BYUB Config', 'A folder for output log files is required.')
                return
                
        pullfrom = self.apic_or_file.get()
        if pullfrom == "not selected":
            messagebox.showerror("Error", "You must choose APIC-EM or a File as input source!")
        elif pullfrom == "apic-em":
            apicip = self.apicip_Text.get()
            apicuser = self.apicuser_Text.get()
            apicpass = self.apicpass_Text.get()
            apicsearchtag = self.devicelistapic_Text.get()
            messagebox.showinfo('glspi','Press OK to begin!\nCheck command prompt for output.')
            AP.apic_run_commands(apicip,apicuser,apicpass,apicsearchtag,username,password,configpath,commandlist)
            return
        elif pullfrom == "file":
            devices = self.devicelistfile_Text.get('1.0', 'end').strip('\n')
            print(devices)
            if devices == '':
                messagebox.showinfo('glspi', 'No devices were found!')
                return
            
            messagebox.showinfo('glspi','Press OK to begin!\nCheck command prompt for output.')
            FI.gather_configs(devices,configpath,username,password,commandlist)
            return
            
