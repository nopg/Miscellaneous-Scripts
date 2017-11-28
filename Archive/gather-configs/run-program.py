from tkinter import Tk

import layout
import gather_configs

root = Tk()
myWindow = layout.MainWindow(root)
myWindow.grid()
root.mainloop()
