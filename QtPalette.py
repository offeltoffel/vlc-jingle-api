#! /usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import sys, os
import vlc
import numpy as np
from threading import Thread, Event
import pathlib

class Jingles:

    def __init__(self, gui):
        
        self.gui = gui
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
            print self.nfiles

#     def newjingle(self):
#         if self.gui.player:
#             self.gui.stop_jingle(event=None)
#         p = pathlib.Path(os.path.expanduser("~"))
#         fullnames = QFileDialog.getOpenFilename(parent=None, caption="Open New Jingle", directory=p)
#         fullnames = list(fullnames)
#         len_new = len(fullnames)
#         for fullname in fullnames:
#             if os.path.isfile(fullname):
#                 if self.gui.bheight == 2 and self.gui.maxbuttons[0] <= self.nfiles[self.gui.activepalette]:
#                     self.gui.bheight = 1
#                 if self.gui.bheight == 1 and self.gui.maxbuttons[1] <= self.nfiles[self.gui.activepalette]:
#                     QMessageBox.critical(self.gui, "Too many jingles", "The number of jingles does not fit on the screen. Omitting %i jingles" % len_new)
#                     break
#                 self.allfiles[self.gui.activepalette].append(fullname)
#                 self.button_names[self.gui.activepalette].append(os.path.basename(fullname).split(".")[0])
#                 self.nfiles[self.gui.activepalette] += 1
#                 len_new -= 1
#
#         self.gui.generate_buttons(ipal=self.gui.activepalette)
#         self.change_flag = True
#
#     def add_palette(self, pname, frm):
#         self.palette_names.append(pname)
#         self.button_names.append([])
#         self.allfiles.append([])
#         self.nfiles.append(0)
#         self.npalettes += 1
#         self.gui.generate_palettes(self.npalettes)
#         self.gui.palette_click(self.npalettes - 1)
#         self.gui.frame_flag = True
#         self.change_flag = True
#         frm.destroy()
#
#     def delete_jingle(self, jid):
#         if self.gui.player:
#             self.gui.stop_jingle(event=None)
#
#         del self.allfiles[self.gui.activepalette][jid]
#         del self.button_names[self.gui.activepalette][jid]
#         self.nfiles[self.gui.activepalette] -= 1
#         self.gui.generate_buttons(ipal=self.gui.activepalette)
#         self.change_flag = True
#
#     def delete_palette(self, pid):
#
#         result = tkMessageBox.askyesno("Delete", "This will delete the selected palette together with all jingles it contains. Do you want to proceed?", icon='warning')
#         if result:
#             if self.gui.player:
#                 self.gui.stop_jingle(event=None)
#
#             del self.allfiles[pid]
#             del self.button_names[pid]
#             del self.nfiles[pid]
#             self.npalettes -= 1
#
#             self.gui.generate_palettes(n=self.npalettes)
#             self.change_flag = True
#             self.gui.palette_click(idx=pid-1)
#
# class ttkTimer(Thread):
#     def __init__(self, callback, tick):
#         Thread.__init__(self)
#         self.callback = callback
#         self.stopFlag = Event()
#         self.tick = tick
#         self.iters = 0
#
#     def run(self):
#         while not self.stopFlag.wait(self.tick):
#             self.iters += 1
#             self.callback()
#
#     def stop(self):
#         self.stopFlag.set()
#
#     def get(self):
#         return self.iters

class JPalette_GUI:
    def __init__(self, gui, jingles):
        self.gui = gui
        self.jingles = jingles
        self.initial_values()
        self.connections()
        self.add_stuff()

    def initial_values(self):
        print "Initialized JPalette_GUI"

    def connections(self):
        self.gui.pushButton_2.clicked.connect(lambda: self.gui.close())

    def add_stuff(self):
        print "adding tabs"
        typetab = QTabWidget()
        tab = QWidget()
        typetab.addTab(tab, "hallo")
        typetablayout = QGridLayout()
        for i in range(3):
            button = QPushButton("Button %i" % i)
            button.setObjectName("cmdButton %i" % i)
            typetablayout.addWidget(button)
        typetab.setLayout(typetablayout)

class MainUiFunction:
    def __init__(self):
        pathUI = os.path.join(os.path.dirname(__file__), 'Jpalette.ui')
        self.gui = uic.loadUi(pathUI)
        jingles = Jingles(gui=self.gui)
        jpalette = JPalette_GUI(gui=self.gui, jingles=jingles)

    def show(self):
        self.gui.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    m = MainUiFunction()
    m.show()
    app.exec_()
    app.quit()
