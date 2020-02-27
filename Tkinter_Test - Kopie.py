#! /usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
from tkFileDialog import askopenfilename, askopenfilenames
import tkMessageBox
import vlc
import numpy as np
from threading import Thread, Event
import pathlib
import os

class Jingles:

    def __init__(self):

        self.allfiles = []
        self.palette_names = [] # Name aller Paletten
        self.button_names = [] # Name aller Buttons
        self.nfiles = [] # Number of files per Palette
        self.npalettes = 0 # Number of Palettes
        self.change_flag = False

    def get_jingles(self):
        # Read jingle-File
        with open('jingles2.txt', 'r+') as jingle_file:
            self.fileraw = jingle_file.readlines()
            self.fileraw = [line.rstrip('\n') for line in self.fileraw]

            ii = -1
            for line in self.fileraw:
                if line.startswith("palette"):
                    self.npalettes += 1
                    self.palette_names.append(line.split(':')[1])
                    self.allfiles.append([])
                    self.button_names.append([])
                    ii += 1
                    continue
                else:
                    self.allfiles[ii].append(line.split(";")[0])
                    self.button_names[ii].append(line.split(";")[1])

            self.nfiles = [len(self.allfiles[i]) for i in xrange(self.npalettes)]

    def newjingle(self):
        if gui.player:
            gui.stop_jingle(event=None)
        p = pathlib.Path(os.path.expanduser("~"))
        fullnames = askopenfilenames(initialdir=p, title="choose your file",
                                   filetypes=(("all files", "*.*"), ("mp4 files", "*.mp4")))
        fullnames = list(fullnames)
        len_new = len(fullnames)
        for fullname in fullnames:
            if os.path.isfile(fullname):
                if gui.bheight == 2 and gui.maxbuttons[0] <= Instance_J.nfiles[gui.activepalette]:
                    gui.bheight = 1
                if gui.bheight == 1 and gui.maxbuttons[1] <= Instance_J.nfiles[gui.activepalette]:
                    tkMessageBox.showinfo("Too many jingles",
                                          "The number of jingles does not fit on the screen. Omitting %i jingles" % len_new)
                    break
                Instance_J.allfiles[gui.activepalette].append(fullname)
                Instance_J.button_names[gui.activepalette].append(os.path.basename(fullname).split(".")[0])
                Instance_J.nfiles[gui.activepalette] += 1
                len_new -= 1

        gui.generate_buttons(ipal=gui.activepalette)
        self.change_flag = True

    def add_palette(self, pname, frm):
        self.palette_names.append(pname)
        self.button_names.append([])
        self.allfiles.append([])
        self.nfiles.append(0)
        self.npalettes += 1
        gui.generate_palettes(self.npalettes)
        gui.palette_click(self.npalettes - 1)
        gui.frame_flag = True
        self.change_flag = True
        frm.destroy()

    def delete_jingle(self, jid):
        if gui.player:
            gui.stop_jingle(event=None)

        del self.allfiles[gui.activepalette][jid]
        del self.button_names[gui.activepalette][jid]
        self.nfiles[gui.activepalette] -= 1
        gui.generate_buttons(ipal=gui.activepalette)
        self.change_flag = True

    def delete_palette(self, pid):

        result = tkMessageBox.askyesno("Delete", "This will delete the selected palette together with all jingles it contains. Do you want to proceed?", icon='warning')
        if result:
            if gui.player:
                gui.stop_jingle(event=None)

            del self.allfiles[pid]
            del self.button_names[pid]
            del self.nfiles[pid]
            self.npalettes -= 1

            gui.generate_palettes(n=self.npalettes)
            self.change_flag = True
            gui.palette_click(idx=pid-1)

class ttkTimer(Thread):
    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

class GUI(Frame, Jingles):

    def __init__(self,parent,title=NONE):
        Frame.__init__(self,parent)
        self.parent = parent
        self.screen_height = self.parent.winfo_screenheight()

        if title is None:
            title = "PyJingle"
        self.parent.title(title)
        self.childwindow = None

        self.player = None

        self.set_params()
        self.widgets()
        self.bindings()

        self.palette_click(0)

        # Timer:
        self.timer = ttkTimer(self.OnTimer, self.timertick)
        self.timer.start()

    def set_params(self):
        self.ncols = 8
        self.bheight = 2
        self.n_palettes = 5
        self.maxbuttons = self.get_nbuttons()
        self.frame_flag = True
        self.lblFile = None
        self.erename = None
        self.default_volume = 100
        self.chkState = 0

        self.jbuttons = []
        self.pbuttons = []
        self.button = None
        self.fullname = ''
        self.activebutton = None
        self.activepalette = None
        self.fadeout = -1
        self.timertick = 0.1 # sec
        self.fadeoutsec = 5
        self.playingjingle = [-1]*4 #0: palette, 1: button, 2: length, 3: time

        self.newpalette = None
        self.newbutton = None


    def widgets(self):
        self.button_frame = Frame(self.parent)
        for i in xrange(self.ncols):
            self.button_frame.columnconfigure(i, weight=1)
        self.button_frame.pack(fill=X, side=TOP, pady=10, padx=10)



        self.palette_names_frame = Frame(self.parent)
        self.palette_names_frame.pack(fill=X, pady=10)

        self.time_frame = Frame(self.parent)
        self.time_frame.columnconfigure(0, weight=1)
        self.time_frame.columnconfigure(1, weight=1)
        self.time_frame.pack(fill=X, padx=15)

        self.lblTimeLeft = Label(self.time_frame, text="-00:00:00", font="Verdana 12 bold")
        self.lblTimeThru = Label(self.time_frame, text="00:00:00", font="Verdana 12 bold")
        self.lblTimeThru.grid(row=0, column=0, sticky=W)
        self.lblTimeLeft.grid(row=0, column=1, sticky=E)


        self.time_bar = Frame(self.parent, bd=1, relief="sunken", height=20)
        self.time_bar.pack(fill=X, padx=15)
        self.time_innerframe = Frame(self.time_bar, width=0, height=20)
        self.time_innerframe.pack_propagate(0)
        self.time_innerframe.grid()

        self.lblTime = Label(self.time_innerframe, text="", fg="white", bg="blue")
        self.lblTime.pack(fill=X)

        self.bottom_frame = Frame(self.parent)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=2)
        self.bottom_frame.pack(fill=X)

        self.control_frame1 = Frame(self.bottom_frame)
        self.control_frame1.grid(row=0, column=0, pady=15)

        self.control_frame2 = Frame(self.bottom_frame)
        self.control_frame2.grid(row=0, column=1, pady=15)

        self.control_frame1.columnconfigure(0, weight=1)
        self.control_frame1.columnconfigure(1, weight=1)

        self.control_frame2.rowconfigure(0, weight=1)
        self.control_frame2.rowconfigure(1, weight=1)
        self.control_frame2.rowconfigure(2, weight=1)


        for i in xrange(self.ncols):
            self.button_frame.columnconfigure(i, weight=1)

        for i in xrange(Instance_J.npalettes):
            self.palette_names_frame.columnconfigure(i, weight=1)

        self.generate_palettes(Instance_J.npalettes)

        Button(self.control_frame1, text="New Jingle", command=self.newjingle).grid(row=0, column=0, ipadx=10,padx=20, sticky=W+E)
        Button(self.control_frame1, text="New Palette", command= lambda: self.child_nameP(event=None, pid=None))\
                                                                        .grid(row=1, column=0, ipadx=10, padx=20, sticky=W+E)
        Button(self.control_frame1, text="Save Palettes", command=self.patternsave).grid(row=0, column=1, ipadx=10,
                                                                                       padx=20, pady=5, sticky=W+E)
        Button(self.control_frame1, text="Quit", command=self._quit).grid(row=1, column=1, sticky=E+W, ipadx=10, padx=20)

        Button(self.control_frame2, text="<", command= lambda: self.change_settings(type="volume", change="down")).grid(row=0, column=0)
        self.lblCurrentVol = Label(self.control_frame2, text=str(self.default_volume))
        self.lblCurrentVol.grid(row=0, column=1, padx=5) # disable while fadeout!
        Button(self.control_frame2, text=">", command= lambda: self.change_settings(type="volume", change="up")).grid(row=0, column=2, pady=5)
        Label(self.control_frame2, text="Current volume").grid(row=0, column=3, sticky=W, pady=5, padx=(5,0))

        Button(self.control_frame2, text="<", command= lambda: self.change_settings(type="fadeout", change="down")).grid(row=1, column=0)
        self.lblFadeout = Label(self.control_frame2, text=str(self.fadeoutsec))
        self.lblFadeout.grid(row=1, column=1)
        Button(self.control_frame2, text=">", command= lambda: self.change_settings(type="fadeout", change="up")).grid(row=1, column=2, pady=5)
        Label(self.control_frame2, text="seconds to fadout").grid(row=1, column=3, sticky=W, padx=(5,0))

    def popup(self, event, type, id):
        if type=="button":
            bmenu = Menu(self.parent, tearoff=0)
            bmenu.add_command(label="Edit jingle", command=lambda event=None, jid=id: self.child_renameJ(event, jid))
            bmenu.add_command(label="Delete jingle", command=lambda jid=id: Instance_J.delete_jingle(jid))
            bmenu.post(event.x_root, event.y_root)
        elif type=="palette":
            pmenu = Menu(self.parent, tearoff=0)
            pmenu.add_command(label="Rename palette", command=lambda event=None, pid=id: self.child_nameP(event, pid))
            pmenu.add_command(label="Delete palette", command=lambda pid=id: Instance_J.delete_palette(pid))
            pmenu.post(event.x_root, event.y_root)

    def get_nbuttons(self):
        buttonheight2 = Button(root, text="A", height=2).winfo_reqheight()  # Test-button
        buttonheight1 = Button(root, text="A", height=1).winfo_reqheight()

        allowed_nrows2 = int(((self.screen_height*0.9 - self.parent.winfo_reqheight()) // buttonheight2) * self.ncols)
        allowed_nrows1 = int(((self.screen_height*0.9 - self.parent.winfo_reqheight()) // buttonheight1) * self.ncols)

        return allowed_nrows2, allowed_nrows1


    def bindings(self):
        self.parent.bind("<space>", lambda event: self.fade_stop(event))
        self.parent.bind("<Control-space>", lambda event: self.stop_jingle(event))
        self.parent.bind("<Control-s>", lambda event: self.patternsave(event))
        self.parent.bind("<Control-q>", lambda event: self._quit(event))
        self.parent.bind("<Up>", lambda event, type="volume", change="up": self.change_settings(type=type, change=change))
        self.parent.bind("<Down>", lambda event, type="volume", change="down": self.change_settings(type=type, change=change))

    def _quit(self, event=None):

        if Instance_J.change_flag == True:
            result = tkMessageBox.askyesno("Save before quit?", "Changes have been made to the pattern. Do you want to save your pattern before quitting?", icon="warning")
            if result: self.patternsave(event=None, dialog=False)

        root.quit()
        root.destroy()
        os._exit(1)

    def OnTimer(self):
        if self.player == None:
            self.lblTime.config(text="")
            return

        self.playingjingle[2] = self.player.get_length()
        self.playingjingle[3] = self.player.get_time()

        try:
            current_jinglestate = float(self.playingjingle[3]) / float(self.playingjingle[2])
        except ZeroDivisionError:
            current_jinglestate = 0.0

        red = current_jinglestate*510
        green = (1-current_jinglestate)*510
        self.time_innerframe.config(width=int(self.time_bar.winfo_width() * current_jinglestate))
        self.lblTime.config(bg='#%02x%02x%02x' % (self.clamp(red), self.clamp(green), self.clamp(0)))

        str_left, str_thru = self.timer_format()
        self.lblTimeLeft.config(text=str_left)
        self.lblTimeThru.config(text=str_thru)

        if self.fadeout > 0:
            self.player.audio_set_volume(self.fadeout)
            self.fadeout -= int((self.default_volume*self.timer.tick) / self.fadeoutsec)
            if self.fadeout <= 0:
                self.stop_jingle(event=None)
                return

    def clamp(self, x):
        return max(0, min(x, 255))

    def timer_format(self):
        time_left = (self.playingjingle[2] - self.playingjingle[3]) / 1000.0
        time_thru = self.playingjingle[3] / 1000.0
        min_left = '{:02d}'.format(int(time_left // 60))
        min_thru = '{:02d}'.format(int(time_thru // 60))
        sec_left = '{:05.2f}'.format(time_left % 60) # {: immer, 05 -> numbers to pad, 2f -> decimal digits
        sec_thru = '{:05.2f}'.format(time_thru % 60)

        str_left = "-" + min_left + ":" + sec_left
        str_thru = min_thru + ":" + sec_thru

        return str_left, str_thru

    def change_settings(self, type, change, event=None):
        if type == "volume" and self.fadeout < 0:
            if change == "up":
                if not self.default_volume >= 100: self.default_volume += 1 #super fancy: ButtonPress-1 aktiviert Timer, der immer schneller tickt, ButtonRelease-1 beendet Timer
            elif change == "down":
                if not self.default_volume <= 0: self.default_volume -= 1
        elif type == "fadeout":
            if change == "up": self.fadeoutsec += 1
            elif change == "down":
                if not self.fadeoutsec == 1: self.fadeoutsec -= 1

        self.lblCurrentVol.config(text=str(self.default_volume))
        self.lblFadeout.config(text=str(self.fadeoutsec))


    def generate_palettes(self, n):
        for old_pbutton in self.pbuttons:
            old_pbutton.destroy()
        if Instance_J.npalettes == 0: return
        self.pbuttons = []

        for i in xrange(n):
            self.newpalette = Button(self.palette_names_frame, text=Instance_J.palette_names[i],
                                command=lambda name=i: self.palette_click(name),
                                width=10, height=2)
            self.newpalette.bind("<Button-3>", lambda event, type="palette", id=i: self.popup(event,type,id))
            self.newpalette.grid(row=0, column=i, sticky=W + E, pady=5, padx=5)
            self.pbuttons.append(self.newpalette)

    def palette_click(self, idx):

        self.button = self.pbuttons[idx]
        self.activepalette = idx
        if Instance_J.nfiles[self.activepalette] > self.maxbuttons[0]: self.bheight = 1

        for button in self.pbuttons:
            button.config(relief='raised')

        self.button.config(relief='sunken')

        self.generate_buttons(ipal=idx)
        if self.playingjingle[0] == idx:
            self.jbuttons[self.playingjingle[1]].config(bg="blue")


    def generate_buttons(self, ipal):
        for old_button in self.jbuttons:
            old_button.destroy()
        self.parent.update()
        if Instance_J.nfiles[ipal] == 0: return
        self.jbuttons = []

        for i in xrange(Instance_J.nfiles[ipal]):
            row = i // self.ncols
            col = i % self.ncols

            self.newbutton = Button(self.button_frame, wraplength=150, text=Instance_J.button_names[ipal][i],
                                    command=lambda jid=i: self.play_jingle(jid), height=self.bheight)

            self.newbutton.bind("<Button-3>", lambda event, type="button", id=i: self.popup(event,type,id))
            self.newbutton.grid(row=row, column=col, sticky=W + E)
            # self.newbutton.update()
            self.jbuttons.append(self.newbutton)
        self.bheight = 2

    def play_jingle(self, jid):
        self.stop_jingle(event=None)
        self.button = self.jbuttons[jid]
        if self.activebutton == self.button: return
        self.activebutton = self.button
        self.button.config(bg="blue")
        print "Playing jingle #%i" % jid

        self.player = Instance.media_player_new()
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.lead_out)
        self.Media = Instance.media_new(Instance_J.allfiles[self.activepalette][jid])
        self.player.set_media(self.Media)
        self.player.play()
        self.playingjingle[0] = self.activepalette
        self.playingjingle[1] = jid
        self.player.audio_set_volume(self.default_volume)

    def stop_jingle(self, event):
        try:
            self.player.stop()
            self.lead_out(event=None)
        except:
            pass

    def fade_stop(self, event):
        if self.player:
            print "Fade to black"
            self.fadeout = self.default_volume

    def lead_out(self,event):
        if not self.playingjingle[1] > len(self.jbuttons):
            self.jbuttons[self.playingjingle[1]].config(bg="SystemButtonFace")
        self.playingjingle = [-1] * 4
        self.activebutton = None
        self.player.audio_set_volume(self.default_volume)
        self.fadeout = -1
        self.player = None
        self.time_innerframe.config(width=0)
        self.lblTime.config(bg="blue")
        self.lblTimeLeft.config(text="-00:00:00")
        self.lblTimeThru.config(text="00:00:00")
        print "Lead Out: Done!"

    def assign_jingle(self, jid):
        p = pathlib.Path(os.path.expanduser("~"))
        fullname = askopenfilename(initialdir=p, title="choose your file",
                                   filetypes=(("all files", "*.*"), ("mp4 files", "*.mp4")))

        if os.path.isfile(fullname):
            Instance_J.allfiles[self.activepalette][jid] = fullname
            Instance_J.change_flag = True

        self.childwindow.focus_set()
        self.lblFile.config(text=fullname)
        self.erename.delete(0,'end')
        self.erename.insert(0, os.path.basename(fullname).split('.')[0])

    def child_renameJ(self, event, jid):
        if self.frame_flag:
            self.childwindow = Toplevel(root)
            frmChange = self.childwindow
            frame1 = Frame(frmChange)
            frame2 = Frame(frmChange)
            frame3a = Frame(frmChange)
            frame3i = Frame(frame3a)
            frame3a.columnconfigure(0,weight=2)
            frame3a.columnconfigure(1,weight=3)
            frame3a.columnconfigure(2,weight=2)
            frame3i.columnconfigure(0, weight=1)
            frame3i.columnconfigure(1, weight=1)
            frame3i.columnconfigure(2, weight=1)
            frame1.pack(pady=10, fill=X)
            frame2.pack(pady=10, fill=X)
            frame3a.pack(pady=10, fill=X)
            frame3i.grid(row=0, column=1, sticky=W+E)
            Label(frame1, text="Jingle-Name:").grid(row=0, column=0, sticky=W, padx=(10,20))
            self.erename = Entry(frame1)
            self.erename.insert(0, os.path.basename(Instance_J.allfiles[self.activepalette][jid]).split('.')[0])
            self.erename.focus_set()
            self.erename.grid(row=0, column=1, sticky=W)
            Label(frame2, text="Jingle-Path:").grid(row=1, column=0, padx=(10,25))
            self.lblFile = Label(frame2, text=Instance_J.allfiles[self.activepalette][jid])
            self.lblFile.grid(row=1, column=1, padx=(0,10))
            Button(frame3i, text="Assign Jingle", command= lambda: self.assign_jingle(jid=jid))\
                .grid(row=0, column=0, sticky=W+E, padx=5)
            b = Button(frame3i, text="OK", default="active", command= lambda: self.rename(id=jid, newtext=self.erename.get(),
                                                                   frm=frmChange, j_or_p="j"))
            b.grid(row=0, column=1, sticky=W+E, padx=5)
            frmChange.bind('<Return>', lambda e, b=b: b.invoke())
            Button(frame3i, text="Abbrechen", command= lambda: self.cancel(frmChange)).grid(row=0, column=2,sticky=W+E, padx=5)
            self.frame_flag = False

    def child_nameP(self, event, pid=None):
        if self.frame_flag:
            frmNameP = Toplevel(root)
            frame1 = Frame(frmNameP)
            frame2a = Frame(frmNameP)
            frame2i = Frame(frame2a)
            frame2a.columnconfigure(0,weight=3)
            frame2a.columnconfigure(1, weight=2)
            frame2a.columnconfigure(2, weight=3)
            frame2i.columnconfigure(0, weight=1)
            frame2i.columnconfigure(1, weight=1)
            frame1.pack(pady=10, fill=X)
            frame2a.pack(pady=10, fill=X)
            frame2i.grid(row=0, column=1, sticky=W+E)

            Label(frame1, text="Palette-Name:").grid(row=0, column=0, sticky=W, padx=(10,20))
            self.erename = Entry(frame1)
            if not pid is None: self.erename.insert(0, Instance_J.palette_names[pid])
            self.erename.focus_set()
            self.erename.grid(row=0, column=1, sticky=W, padx=(0,10))
            if pid is None:
                b = Button(frame2i, text="OK", default="active", command=lambda: Instance_J.add_palette(pname=self.erename.get(), frm=frmNameP))
                b.grid(row=0, column=0, sticky=W+E)
            else:
                b = Button(frame2i, text="OK", default="active", command=lambda: self.rename(id=pid, newtext=self.erename.get(),
                                                   frm=frmNameP, j_or_p="p"))
                b.grid(row=0, column=0, sticky=W+E)
            Button(frame2i, text="Abbrechen", command=lambda: self.cancel(frmNameP)).grid(row=0, column=1, sticky=W+E)
            frmNameP.bind('<Return>', lambda e, b=b: b.invoke())
            self.frame_flag = False

    def rename(self, id, newtext, frm, j_or_p):
        if j_or_p=="j":
            self.button = self.jbuttons[id]
            Instance_J.button_names[self.activepalette][id] = newtext
        elif j_or_p=="p":
            self.button = self.pbuttons[id]
            Instance_J.palette_names[id] = newtext
        self.button.config(text = newtext)
        self.frame_flag = True
        Instance_J.change_flag = True
        frm.destroy()


    def patternsave(self, event=None, dialog=True):
        with open('jingles2.txt', 'w') as jingle_file:
            for pal_no in xrange(len(Instance_J.allfiles)):
                jingle_file.write("palette:"+Instance_J.palette_names[pal_no]+"\n")
                for ji_no in xrange(len(Instance_J.allfiles[pal_no])):
                    jingle_file.write(Instance_J.allfiles[pal_no][ji_no]+";"+
                                      Instance_J.button_names[pal_no][ji_no]+"\n")
        if dialog: tkMessageBox.showinfo("Pattern saved", "The pattern was successfully saved!")

    def cancel(self, frm):

        self.frame_flag = True
        frm.destroy()

Instance = vlc.Instance()
Instance_J = Jingles()
Instance_J.get_jingles()

root = Tk()
gui = GUI(root,title="PyJingle")
root.mainloop()