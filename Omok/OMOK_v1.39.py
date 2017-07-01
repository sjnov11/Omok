# -*- coding: cp949 -*-

import wx
import string
import unicodedata
import os
import time
import hashlib
import thread
import sys
import random

TITLE = "OMOK v1.39"


class PasswordFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self,None,title=TITLE,size=(205,75))
		self.count = 0
		wx.StaticText(self,-1,"PW: ",pos=(5,10))
		self.SetBackgroundColour('white')
		self.pwCtrl = wx.TextCtrl(self,-1,"",size=(145,23),pos=(30,5),style=wx.TE_PASSWORD)
		self.pwCtrl.SetInsertionPoint(0)
		self.Bind(wx.EVT_TEXT_ENTER,self.OnOK)


	def OnOK(self,event):
		self.count+=1
		if self.count >2:
			wx.MessageBox("Too many failures. Shutting Down ...", "Sorry")
		else:
			#Password : 기리보이
			password = self.pwCtrl.GetValue()
			hashpass = hashlib.sha512(password).hexdigest()
			if hashpass == 'acaef4c899731b2dcde63ab4e3ed6b920d22c516e9f916aaef1de5f0b119a3358dd8d615d57b03aecaac849f4fcd53fcd79ff578a3ff85ebb5a6131a77fb04b0':
				rframe = RoomFrame()
				rframe.Show()
				self.Close()
			else:
				wx.MessageBox("Wrong Password. Try Again","Sorry",wx.OK | wx.ICON_INFORMATION)



class RoomFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self,None,title=TITLE,size=(225,125))
		self.panel = wx.Panel(self)
		self.panel.SetBackgroundColour('white')
		self.roomLabel = wx.StaticText(self.panel,-1,"Room Number:",pos=(7,7))
		self.room = wx.TextCtrl(self.panel,-1,"",size=(100,20),pos=(100,5),style=wx.TE_RICH)
		self.nameLabel = wx.StaticText(self.panel,-1,"Nick Name:",pos=(7,30))
		self.name = wx.TextCtrl(self.panel,-1,"",size=(100,20),pos=(100,30),style=wx.TE_RICH)
		self.button = wx.Button(self.panel,-1,"OK",size=(70,22),pos=(130,55))
		self.Bind(wx.EVT_BUTTON,self.okButton,self.button)

	def okButton(self,event):
		roomNum = self.room.GetValue().encode('cp949')
		nickName = self.name.GetValue().encode('cp949')
		if roomNum == '' or nickName == '':
			wx.MessageBox("Fill the Room Number and Nick Name", "ERROR", wx.OK | wx.ICON_INFORMATION)
		else:
			self.room = Room(roomNum,nickName)
			self.room.makeRoom()
			wframe = WaitingFrame(self.room)
			wframe.Show()
			self.Close()


class WaitingFrame(wx.Frame):
	def __init__(self,croom):
		wx.Frame.__init__(self,None,title=TITLE,size=(210,200))
		self.panel = wx.Panel(self)
		self.panel.SetBackgroundColour('white')
		self.room = croom
		self.userlist=[]
		self.buserlist=[]
		self.check=[]
		wx.StaticText(self.panel,-1,"[ "+self.room.roomnum+" ]",pos=(20,7))
		wx.StaticText(self.panel,-1,"- User -",pos=(20,35))
		self.listbox = wx.ListBox(self.panel,-1,(20,52),(150,50),self.userlist,wx.LB_SINGLE)
		self.button = wx.Button(self.panel,-1,"Play",pos=(82,115))
		self.Bind(wx.EVT_BUTTON,self.startbutton,self.button)
		self.Bind(wx.EVT_CLOSE,self.OnClose)
		self.start = False

		thread.start_new_thread(self.getuserlist,())

	def getuserlist(self):
		while not self.start:
			self.userlist = self.room.readUserlist()
			if self.buserlist != self.userlist:
				self.check = []
				self.buserlist = []
				self.listbox.Clear()
			for user in self.userlist:
				if user not in self.check:
					self.listbox.Append(user)
					self.check.append(user)
					self.buserlist.append(user)

	def startbutton(self,event):
		if len(self.check) ==2 :
			self.start = True
			mframe = MainFrame(self.room)
			mframe.Show()
			#thread.exit()
			self.Destroy()
		if len(self.check) <2:
			wx.MessageBox("Please wait for your opponent","Wait...",wx.OK | wx.ICON_INFORMATION)
		if len(self.check) >2:
			wx.MessageBox("Too many users in this room","Can't Play...",wx.OK | wx.ICON_INFORMATION)

	def OnClose(self,event):
		#try:
		#except:
		#	pass
		#thread.exit()

		self.start = True
		try:
			self.room.deleteFile()
		except:
			pass
		self.Destroy()



class MainFrame(wx.Frame):
	def __init__(self,room):
		wx.Frame.__init__(self,None,title=TITLE,size=(420,480))
		self.statusbar = self.CreateStatusBar()
		self.positiontuple = (0,0)
		self.room = room
		self.t_list=[]
		self.draw_list=[]
		self.setting = False

		#Turn : Black/0  , White/1
		self.playerturn = self.check_playerturn()
		self.BLACK = 0
		self.WHITE = 1
		self.SWITCH = 0
		self.SWITCH2 = 0
		self.TURN = self.BLACK
		self.HIDE = 20
		self.UNHIDE = 250
		self.TRANSPARENT = 10
		self.GAMING = True

		popup1 = wx.NewId()
		popup2 = wx.NewId()
		popup3 = wx.NewId()

		#Accelerator(short-key) Assignment
		#acceltbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('R'), popup1),(wx.ACCEL_NORMAL, ord('H'), popup2), (wx.ACCEL_NORMAL, ord('U'), popup3)])
		#341 = F2 key
		acceltbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('R'), popup1),(wx.ACCEL_NORMAL,341,popup2)])

		self.SetAcceleratorTable(acceltbl)

		self.Bind(wx.EVT_MENU, self.OnRestart, id = popup1)
		self.Bind(wx.EVT_MENU, self.OnHide, id = popup2)

		self.Bind(wx.EVT_MOTION, self.OnSketchMotion)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		#self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		thread.start_new_thread(self.drawing,())

	def OnRestart(self,event):
		if not self.GAMING:
			dlg2 = wx.MessageDialog(None, "REGAME?", 'Game Set', wx.YES_NO | wx.ICON_QUESTION)
			retCode2 = dlg2.ShowModal()
			if (retCode2 == wx.ID_YES):
				self.Destroy()
				f=open(self.room.roomnum,'r')
				val = f.readlines()
				f.close()
				if len(val) != 1:
					os.remove(self.room.roomnum)
				f=open(self.room.roomnum,'a+')
				f.write('user:'+self.room.nick+'\n')
				f.close()
				wframe = WaitingFrame(self.room)
				wframe.Show()


	def OnHide(self,event):
		if self.SWITCH == 0 :
			self.SetTransparent(self.HIDE)
			self.SWITCH = 1
		elif self.SWITCH == 1:
			self.SetTransparent(self.UNHIDE)
			self.SWITCH = 0

	def OnTransparent(self,event): pass

	def OnSketchMotion(self,event):
		self.positiontuple = event.GetPositionTuple()
		#self.statusbar.SetStatusText(str(self.positiontuple))
		event.Skip()

	def OnPaint(self,event):
		self.setting = False
		dc = wx.BufferedPaintDC(self)
		self.Draw(dc)

	def Draw(self,dc):
	# Function to draw results on drawing canvas
		if not self.setting:
			font1 = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False, face = u'Times New Roman')
			dc.SetFont(font1)
			dc.SetTextForeground(wx.Colour(255,255,255,255))
			dc.DrawText(TITLE, 10, 10)
			dc.DrawText("By SJ", 360, 400)
			dc.SetPen(wx.Pen(wx.Colour(255,255,255,255),2))
			dc.SetBrush(wx.Brush(wx.Colour(232,232,200,0)))
			dc.DrawRectangle(35,35, 340,340)

			dc.SetPen(wx.Pen("black"))
			for i in range(0, 24):
				dc.DrawLine(40, 40+15*i, 370, 40+15*i)
			for i in range(0, 24):
				dc.DrawLine(40+15*i, 40, 40+15*i, 370)

			self.recvTuple()
			self.draw_list=[]
			self.TURN = self.BLACK

			for tuple in self.t_list:
				if tuple not in self.draw_list :
					if tuple == self.t_list[len(self.t_list)-1]:
						self.draw_pin(tuple,self.TURN,dc,1)
					else:
						self.draw_pin(tuple, self.TURN, dc, 0)
					self.draw_list.append(tuple)
					if self.Check_winner() == self.WHITE:
						thread.exit()
					if self.Check_winner() == self.BLACK:
						thread.exit()
					if self.TURN == self.BLACK:
						self.TURN = self.WHITE
					elif self.TURN == self.WHITE:
						self.TURN = self.BLACK
			self.setting = True


#	def OnRightDown(self, event):
#		object_tuple = self.positiontuple
#		round_tuple = self.tupleround(object_tuple)
#		if self.check_inboard(round_tuple):
#			if round_tuple not in t_list:
#				dc =wx.BufferedDC(wx.ClientDC(self))
#				self.draw_pin(round_tuple, 1, dc)
#				t_list.append(round_tuple)


	def OnLeftDown(self, event):
		if self.GAMING:
			if self.playerturn == self.TURN:
				object_tuple = self.positiontuple
				round_tuple = self.tupleround(object_tuple)
				if self.check_inboard(round_tuple):
					if round_tuple not in self.t_list:
						self.room.writeTuple(round_tuple)

		else: pass




	def drawing(self):
		while True:
			if self.setting:
				self.recvTuple()
				self.draw_pins()
				if self.TURN == 0 :
					list = self.room.readUserlist()
					if len(list) <2 :
						text = "Oppoents left the rooom"
					else:
						text = str(list[0])+" 's Turn"
				elif self.TURN == 1 :
					list = self.room.readUserlist()
					if len(list) <2 :
						text = "Oppoents left the rooom"
					else:
						text = str(list[1])+" 's Turn"

				self.statusbar.SetStatusText(text)
				if self.Check_winner() == self.WHITE:
					self.GAMING = False
					self.ShowWinnerMsg()
					return True

					#thread.exit()
					#print('white')
					#self.ShowWinnerMsg()

				if self.Check_winner() == self.BLACK:
					self.GAMING = False
					self.ShowWinnerMsg()
					return True

					#thread.exit()
					#print('black')
					#self.ShowWinnerMsg()


	def recvTuple(self):
		self.t_list = self.room.readTuplelist()



	def draw_pins(self):
		for tuple in self.t_list:
			if tuple not in self.draw_list:
				dc = wx.BufferedDC(wx.ClientDC(self))
				if len(self.draw_list) >0:
					self.draw_pin(self.draw_list[len(self.draw_list)-1], not self.TURN, dc, 0)
					self.draw_pin(tuple,self.TURN,dc,1)
				else:
					self.draw_pin(tuple,self.TURN,dc,0)

				self.draw_list.append(tuple)

				if self.TURN == self.BLACK:
					self.TURN = self.WHITE
				elif self.TURN == self.WHITE:
					self.TURN = self.BLACK

	def tupleround(self, tuple):
		i, j = tuple
		re_i = i - (i%15) + 10
		re_j = j - (j%15) + 10
		return (re_i, re_j)


	def check_inboard(self,r_tuple):
		re_i, re_j = r_tuple
		if re_i<40 or re_j<40 or re_i>370 or re_j>370:
			return False
		else:
			return True


	def check_draw(self, tuple):
		if tuple not in self.draw_list:
			return True


	def draw_pin(self, pos, kind, dc, last):
		#last 마지막 빨간테두리
		colour = ""
		white = wx.Colour(0, 0, 0, 0)
		black = wx.Colour(255, 255, 255, 255)
		red = wx.Colour(255, 0, 0, 255)

		if kind == 0 :
			if last:
				dc.SetPen(wx.Pen(red,1))
			else:
				dc.SetPen(wx.Pen(black,1))
			dc.SetBrush(wx.Brush(white))
			dc.DrawCircle(pos[0], pos[1], 7)

		if kind == 1 :
			if last:
				dc.SetPen(wx.Pen(red,1))
			else:
				dc.SetPen(wx.Pen(white,1))
			dc.SetBrush(wx.Brush(black))
			dc.DrawCircle(pos[0], pos[1], 7)


	def check_playerturn(self):
		nick = self.room.nick
		userlist = self.room.readUserlist()
		index = 0
		for i in userlist:
			if i == nick :
				return index
			else:
				index = index+1
				return index


	def Check_winner(self):
		self.white_list = []
		self.black_list = []
		for i in range(len(self.draw_list)):
			if i%2 == 0 :
				self.black_list.append(self.draw_list[i])
			if i%2 == 1 :
				self.white_list.append(self.draw_list[i])

		if self.IsTupleFive(self.white_list):
			return self.WHITE
		elif self.IsTupleFive(self.black_list):
			return self.BLACK

		else:
			return -1


	def IsTupleFive(self, list):
		caselist = [(0,-15), (15,-15), (15,0), (15,15), (0,15), (-15,15), (-15,0), (-15,-15)]

		for tuple in list:
			for case in caselist:
				if self.ConnectCount(list,tuple,1,case) == 5:
					tx, ty = case
					rcase = (-tx, -ty)
					if self.ConnectCount(list, tuple, 1, rcase)>1:
						pass
					else:
						return True


	def ConnectCount(self,list,tuple,num,casenum):
		case = casenum
		count = num
		ctuple = self.AroundPosition(tuple,case)
		if ctuple in list:
			return self.ConnectCount(list, ctuple, count+1, case)
		else :
			return count

	def AroundPosition(self, tuple, case):
		tx, ty = tuple
		cx, cy = case
		atuple = (tx+cx, ty+cy)
		return atuple


	def OnClose(self,event):
		try:
			self.room.deleteFile()
		except:
			pass
		thread.exit()
		self.Close()


	def ShowWinnerMsg(self):
		if self.Check_winner() == self.WHITE:
			list = self.room.readUserlist()
			dlg = wx.MessageDialog(None, str(list[1])+" is Win", 'Game Set', wx.OK | wx.ICON_QUESTION)
			retCode = dlg.ShowModal()
			#self.ShowRegameMsg()


		if self.Check_winner() == self.BLACK:
			list = self.room.readUserlist()
			dlg = wx.MessageDialog(None, str(list[0])+" is Win", 'Game Set', wx.OK | wx.ICON_QUESTION)
			retCode = dlg.ShowModal()
			#self.ShowRegameMsg()


#	def ShowRegameMsg(self):
#		dlg2 = wx.MessageDialog(None, "re?", 'Game Set', wx.YES_NO | wx.ICON_QUESTION)
#		retCode2 = dlg2.ShowModal()
#		if (retCode2 == wx.ID_YES):
#			print("YES REGAME")
#
#			wframe = WaitingFrame(self.room)
#			wframe.Show()
#			thread.exit()
# 		if (retCode2 == wx.ID_YES):
#			print("GGG")
#			if len(self.room.readTuplelist())>0:
#				try:
#					os.remove(self.room.roomnum)
#				except:
#					pass
#			f= open(self.room.roomnum, 'a+')
#			f.write("user:"+self.room.nick+'\n')
#			f.close()
#			print('done')
#			self.Destroy()

#		else:
#			self.room.deleteFile()


class Room():
	def __init__(self,room,nick):
		self.roomnum = room
		self.nick = nick

	def makeRoom(self):
		if os.getcwd!='gdata':
			try:
				os.mkdir('gdata')
			except:
				pass

		if os.getcwd!='gdata':
			os.chdir('gdata')
		f=open(self.roomnum,'a+')
		while True:
			if self.nick in self.readUserlist():
				self.nick = self.nick+'1'
			else:
				break
		f.write("user:"+self.nick+'\n')
		f.close()


	def readUserlist(self):
		userlist=[]
		try:
			f = open(self.roomnum,'r')
			data = f.readlines()
			f.close()
		except:
			pass
		for user in data:
			if user[0:5] == 'user:':
				userlist.append(user[5:len(user)-1])
		return userlist


	def writeTuple(self,tuple):
		f=open(self.roomnum,'a+')
		f.write(str(tuple)+'\n')
		f.close()

	def readTuplelist(self):
		f=open(self.roomnum,'r')
		data = f.readlines()
		f.close()
		rtuple=[]
		for tuple in data:
			if tuple[:5] == 'user:' : pass
			else:
				temp =[]
				k = tuple[1:len(tuple)-2]
				temp = k.split(', ')
				tx = int(temp[0])
				ty = int(temp[1])
				ttuple = (tx,ty)
				rtuple.append(ttuple)
		return rtuple


	def deleteFile(self):
		if len(self.readUserlist()) == 1:
			try:
				os.remove(self.roomnum)
			except:
				pass

		else:
			f=open(self.roomnum,'r')
			data = f.readlines()
			for list in data:
				if list == 'user:'+self.nick+'\n':
					data.pop(data.index(list))
					break
			f.close()
			f=open(self.roomnum,'w')
			for list in data:
				f.write(list)
			f.close()


class FileManager:
	def __init__(self,room):
		self.filename = room

	def writeFile(self,tuple):
		f=open(self.filename,'a+')
		f.write(str(tuple)+'\n')
		f.close()

	def readFile(self):
		f=open(self.filename,'r')
		val=f.readlines()
		f.close()
		return val


	def deleteFile(self):
		try:
			os.remove(self.filename)
		except:
			pass

class PathManager:
	def __init__(self):
		pass

	def getCurrentPath(self):
		return os.getcwd()

	def changeCurrentPath(self,path):
		os.chdir(path)

	def makeDirectory(self,path):
		try:
			os.mkdir(path)
		except:
			pass

class PlayApp(wx.App):
	def OnInit(self):
		rframe = PasswordFrame()
		rframe.Show()

		return True

#Main Event
app = PlayApp()
app.MainLoop()

