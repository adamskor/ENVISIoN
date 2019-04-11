#
#  ENVISIoN
#
#  Copyright (c) 2019 Anton Hjert
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################################
#
#  Alterations to this file by
#
#  To the extent possible under law, the person who associated CC0
#  with the alterations to this file has waived all copyright and related
#  or neighboring rights to the alterations made to this file.
#
#  You should have received a copy of the CC0 legalcode along with
#  this work.  If not, see
#  <http://creativecommons.org/publicdomain/zero/1.0/>.

"""*****************************************************************************"""
"""This file sets up the Parser-section of the GUI, which is a collapsible pane."""
"""*****************************************************************************"""

import wx, sys, os
import inspect
path_to_current_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.expanduser(path_to_current_folder+'/../'))
sys.path.insert(0, os.path.expanduser(path_to_current_folder+'/../parser/vasp'))
from bandstructure import bandstructure
from doscar import dos
from md import md
from unitcell import unitcell
from volume import charge, elf
from fermi import fermi_surface
from parchg import parchg
from main import *
from generalCollapsible import GeneralCollapsible

class ParserPane(GeneralCollapsible):
    def __init__(self, parent):
        super().__init__(parent, "Parser")

    #Path-selection to file for parsing
        self.fileText = wx.StaticText(self.GetPane(),
                                    label="File to parse:")
        self.chooseParseDir = wx.Button(self.GetPane(), size=self.itemSize,
                                    label = str('..or select folder'))
        self.enterPath = wx.TextCtrl(self.GetPane(), size=self.itemSize,
                                    value="Enter path..",
                                    style=wx.TE_PROCESS_ENTER)
    #Path-selection to folder for saving
        self.folderText = wx.StaticText(self.GetPane(),
                                    label="Save in folder:")       
        self.chooseSaveDir = wx.Button(self.GetPane(), size=self.itemSize,
                                    label = str('..or select folder'))
        self.enterSavePath = wx.TextCtrl(self.GetPane(), size=self.itemSize,
                                    value="Enter path..",
                                    style=wx.TE_PROCESS_ENTER)
    #Visualization-type selection:
        self.typeText = wx.StaticText(self.GetPane(),
                                    label="Type of Visualization:")
        self.selectVis = wx.ComboBox(self.GetPane(), size=self.itemSize,
                                    value = "Select type",
                                    choices= ('All','Bandstructure','DoS',
                                            'Charge','ELF',
                                            'Fermi Surface','MD',
                                            'Parchg','PCF',
                                            'Unitcell'))
        self.parserDict = {
            'Unitcell' : 'unitcell from VASP' ,
            'MD' : 'molecular dynamics from VASP',
            'Charge' : 'charge from VASP',
            'ELF' : 'ELF from VASP',
            'DoS' : 'DOS from VASP',
            'Bandstructure' : 'bandstructure from VASP', 
            'Fermi Surface' : 'fermi surface from VASP',
            'PCF' : 'pair correlation function from VASP',
            'Parchg' : 'Parchg from VASP'
        }

        self.parseFuncDict = {
        'Unitcell': unitcell,
        'MD': md,
        'Charge': charge,
        'ELF': elf,
        'DoS': dos,
        'Bandstructure': bandstructure,
        'Fermi Surface': fermi_surface,
        'PCF' : '',
        'Parchg' : parchg
    }

    #Parse-button
        self.hdf5Text = wx.StaticText(self.GetPane(),
                                    label="Enter new or existing filename:")
        self.hdf5File = wx.TextCtrl(self.GetPane(), size=self.itemSize,
                                    value="(without .hdf5)",
                                    style=wx.TE_PROCESS_ENTER)
        self.parse = wx.Button(self.GetPane(), size=self.itemSize,
                                label = str('Parse'))

    #Text colour settings
        self.fileText.SetForegroundColour(self.text_colour)
        self.folderText.SetForegroundColour(self.text_colour)
        self.typeText.SetForegroundColour(self.text_colour)

    #Variables for paths, type of Visualization and parsing.
        self.path = ""
        self.savePath = ""
        self.visType = 'All'
        self.newFileHdf5 = "NewFile"
        self.hdf5Path = ''
        self.parseOut = None
        
    #Item-addition in pane
        expand_flag = wx.SizerFlags().Expand().Border(wx.ALL, 1)
        self.add_item(self.fileText, sizer_flags=expand_flag)
        self.add_item(self.enterPath, sizer_flags=expand_flag)
        self.add_item(self.chooseParseDir,sizer_flags=expand_flag)
        self.add_item(self.folderText, sizer_flags=expand_flag)
        self.add_item(self.enterSavePath, sizer_flags=expand_flag)
        self.add_item(self.chooseSaveDir,sizer_flags=expand_flag)
        self.add_item(self.typeText, sizer_flags=expand_flag)
        self.add_item(self.selectVis,sizer_flags=expand_flag)
        self.add_item(self.hdf5Text,sizer_flags=expand_flag)
        self.add_item(self.hdf5File,sizer_flags=expand_flag)
        self.add_item(self.parse,sizer_flags=expand_flag)
        
    #Signal-handling for buttons and boxes:
        self.chooseParseDir.Bind(wx.EVT_BUTTON,self.folder_pressed)
        self.enterPath.Bind(wx.EVT_TEXT_ENTER,self.path_OnEnter)
        self.chooseSaveDir.Bind(wx.EVT_BUTTON,self.parse_selected)
        self.enterSavePath.Bind(wx.EVT_TEXT_ENTER,self.savePath_OnEnter)
        self.selectVis.Bind(wx.EVT_COMBOBOX,self.vis_selected)
        self.parse.Bind(wx.EVT_BUTTON,self.parse_pressed)
        self.hdf5File.Bind(wx.EVT_TEXT, self.hdf5_name_enter)
        
#When "File to parse"-select button is pressed
    def folder_pressed(self,event):
        self.path = self.choose_directory("Choose directory with files to parse")
        if not self.path == "":
            self.enterPath.SetValue(self.path)

#When path entered in text and Enter-key is pressed
    def path_OnEnter(self,event):
        self.path = self.directory_if_exists(self.enterPath.GetLineText(0))

#When "Save in folder"-select button is pressed
    def parse_selected(self,event):
        self.savePath = self.choose_directory("Choose output directory")
        if not self.savePath == "":
            self.enterSavePath.SetValue(self.savePath)
    
#When save-path entered in text and Enter-key is pressed
    def savePath_OnEnter(self,event):
        self.savePath = self.directory_if_exists(self.enterSavePath.GetLineText(0))

#When visualization-type is changed
    def vis_selected(self,event):
        self.visType = self.selectVis.GetValue()

#Select the hdf5 file name:
    def hdf5_name_enter(self,event):
        self.newFileHdf5 = self.hdf5File.GetLineText(0)

#When Parse-button is pressed
    def parse_pressed(self,event):
    #Create new hdf5-file if needed
        if not os.path.isfile(self.savePath+'/'+self.newFileHdf5+'.hdf5'):
            open(self.newFileHdf5+'.hdf5',"w+")
    #Parse with suitable function
        if self.visType == 'All':
            self.parseOut = parse_all(self.savePath+'/'+self.newFileHdf5+'.hdf5', self.path)
        elif self.parseFuncDict[self.visType](self.savePath+'/'+self.newFileHdf5+'.hdf5', self.path):
            self.open_message("Parsing "+self.path+
                                " successfully done for "+
                                self.visType+" visualization!",
                                "Succsessfully parsed!")
            return            
    #Check output and put out appropriate message
        #Parse failed:     
        if self.parseOut == None:
            self.open_message("Parsing "+self.path+" failed!",
                        "Failed!")
        #All parsing skipped
        elif not self.parseOut:
            self.open_message("Nothing new to parse!",
                        "Failed!")
        #Possible parsings completed
        else:
            self.open_message("Parsing "+self.path+
                                " successfully done for: "+
                                ', '.join(self.parseOut),
                                "Succsessfully parsed!")
#Return path if the path exists.                        
    def directory_if_exists(self,path):
        if not os.path.exists(path):
            self.open_message(path+" not a valid directory!","Failed!")
            return ""
        else: 
            return path

#Dialog for choosing file in file explorer
    def choose_directory(self,label):
        dirFrame = wx.Frame(None, -1, 'win.py')
        dirFrame.SetSize(0,0,200,50)
        dirDialog = wx.DirDialog(dirFrame, label,
                                 "", style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
        dirDialog.ShowModal()
        path = dirDialog.GetPath()
        dirDialog.Destroy()
        dirFrame.Destroy()
        return path

