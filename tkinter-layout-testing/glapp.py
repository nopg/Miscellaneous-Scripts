import tkinter as tk
from tkinter import ttk

import file_run_commands as fr

TITLE = 'glapp'
MAINWINDOWSIZE = "900x700"

LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Verdana", 10)
SMALL_FONT = ("Verdana", 8)


class GlApp(tk.Tk):

    def __init__(self,parent):
        tk.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        container = tk.Frame(self, background="bisque")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (HomePage, ApicPage, FilePage, TestPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(HomePage)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent, background="blue")

        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)

        button1 = ttk.Button(self, text="> Next >",
                            command=lambda: controller.show_frame(FilePage))
        button1.grid(row=0,column=1,sticky="se",padx=10,pady=10)

        button2 = ttk.Button(self, text="Test",
                            command=lambda: controller.show_frame(TestPage))
        button2.grid(row=0,column=0,padx=10,pady=10)

class TestPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background="gray")

        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(1,weight=1)
        self.grid_columnconfigure(1,weight=1)

        tlFrame = tk.Frame(self, background="red",)
        tlFrame.grid(row=0,column=0, sticky="nsew")

        trFrame = tk.Frame(self, background="blue")
        trFrame.grid(row=0,column=1, sticky="nsew")

        blFrame = tk.Frame(self, background="yellow")
        blFrame.grid(row=1,column=0, sticky="nsew")
        
        brFrame = tk.Frame(self, background="green")
        brFrame.grid(row=1,column=1, sticky="nsew")

        tlFrame.grid_rowconfigure(0, weight=1)
        tlFrame.grid_columnconfigure(0, weight=1)

        brFrame.grid_rowconfigure(0, weight=1)
        brFrame.grid_columnconfigure(0, weight=1)

        spacer1 = ttk.Label(trFrame,text="toprightframe",font=NORM_FONT)
        spacer1.grid(padx=20,pady=20)
        spacer2 = ttk.Label(blFrame,text="bottomleftframe",font=NORM_FONT)
        spacer2.grid(padx=20,pady=20)

        self.label1 = ttk.Label(tlFrame, text="topleftframe", font=NORM_FONT)
        self.label1.grid(padx=20,pady=20)

        label2 = ttk.Label(brFrame, text="bottomrightframe", font=NORM_FONT)
        label2.grid(row = 0, column = 0,padx=20,pady=20)

        button1 = ttk.Button(brFrame, text="< Back <",
                            command=lambda: controller.show_frame(HomePage))
        button1.grid(row=0,column=1,sticky="se",padx=10,pady=10)

        button2 = ttk.Button(brFrame, text="> Next >",
                            command=self.start)
        button2.grid(row=0,column=2,sticky="se",padx=10,pady=10)

    def start(self):
        print("Running start()")
        print("Running gather_configs()")
        teststr = "Testing"
        fr.run_commands(teststr, self.label1)
        print("Finished..")
        return

class FilePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)

        button1 = ttk.Button(self, text="< Back <",
                            command=lambda: controller.show_frame(HomePage))
        button1.grid(row=0,column=1,sticky="se",padx=10,pady=10)

        button2 = ttk.Button(self, text="> Next >",
                            command=lambda: controller.show_frame(HomePage))
        button2.grid(row=0,column=2,sticky="se",padx=10,pady=10)

class ApicPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

if __name__ == "__main__":
    app = GlApp(None)
    app.title(TITLE)
    app.geometry(MAINWINDOWSIZE)
    app.mainloop()
