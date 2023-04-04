from PySide2 import QtWidgets
import shiboken2
import maya.OpenMayaUI as mui
import copy
import os.path
from PySide2.QtCore import QPoint, QRect, QSize, Qt
from PySide2.QtGui import *
from PySide2.QtWidgets import QLabel, QRubberBand

class Window(QLabel):
''' Class to implement drag select functionality '''
    def __init__(self, parent = None, widgets = None, slots = None, colors = None):
    
        QLabel.__init__(self, parent)
        Window.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        Window.origin = QPoint()
        Window.rectPoints = (1,2,3,4)
        Window.isMoving = False
        Window.widgets = widgets
        Window.slots = slots
        Window.colors = colors
    def mousePressEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            Window.isMoving = True
            Window.origin = QPoint(event.pos())
            Window.rubberBand.setGeometry(QRect(Window.origin, QSize()))
            Window.rubberBand.show()
            index = 0
            for button in Window.widgets:
                #print('stopped')
                button.setStyleSheet('background-color:'+Window.colors[index]+';')
                index = index+1
            #print(Window.isMoving)
            maya.cmds.select(clear = True)
            return True
    
    def mouseMoveEvent(self, event):
    
        if not self.origin.isNull():
            Window.isMoving = True
            Window.rubberBand.setGeometry(QRect(Window.origin, event.pos()).normalized())
            Window.rectPoints = QRect(Window.origin, event.pos()).normalized().getRect()
            self.checkOverlap( QRect(Window.origin, event.pos()).normalized())
            #print(Window.isMoving)
            
    
    def mouseReleaseEvent(self, event):
    
        if event.button() == Qt.LeftButton:
            Window.rubberBand.hide()
            Window.isMoving = False
                    
    def createSelection(self,joint):
        maya.cmds.select(str(joint),add=True)
        #print(joint)
        self.changeButtonclr()

    def changeButtonclr(self):
        selected = maya.cmds.ls(selection = True)
        for joint in Window.slots:
            #print(selected)
            if joint in selected:
                index = Window.slots.index(joint)
                button = Window.widgets[index]
                button.setStyleSheet('background-color: green;')


    def checkOverlap(self,rect):
     
        if Window.isMoving == True:
            index = 0
            for button in Window.widgets:
                slot = Window.slots[index]
                x = button.geometry().x()
                y = button.geometry().y()
                if rect.contains(x,y):
                    button.clicked.connect(maya.cmds.select(str(slot),add=True,clear=False))
                    button.setStyleSheet('background-color: white;')
                    #self.changeButtonclr()
                index += 1
class Autopicker:
'''Class to implement the picker '''

    def __init__(self):
        self.colMinWidth = 625.0/51
        self.rowMinHeight = 625.0/45
        self.layoutDim = (625,625)
        self.gridSize = (45,51)
        parent = self.getMayaWindow()
        self.window = QtWidgets.QMainWindow(parent)
        widget = QtWidgets.QWidget()
        widget.setMaximumSize(625,625)
        label = QLabel(widget)

        str = maya.cmds.file(q=True, sn = True)
        index=str.rfind('/')
        path = str[0:index]+"/template_azula.png"
        pixmap = QPixmap(path)
        label.setPixmap(pixmap)

        label.resize(pixmap.width(), pixmap.height())
        self.button_list = []
        self.button_fn_list = []
        self.button_clr_list = []
        self.window.setCentralWidget(widget)
        window2 = Window(widget,self.button_list,self.button_fn_list,self.button_clr_list)
        self.layout = QtWidgets.QGridLayout(widget)
        for col in range(self.gridSize[1]):
            self.layout.setColumnMinimumWidth(col,self.colMinWidth)
            self.layout.setRowMinimumHeight(col,self.rowMinHeight)
        self.selected = "none"
        self.ToSelect = "none"
        self.switchList = self.getSwitches()
        self.controller_list = self.getControllersIK()
        self.finger_list = self.getFingers()
        self.listOfPos = ['a','b']
        self.rowOffset = 1
        self.colOffset = 3
        self.listOfPosRL = ['a','b']
        self.createEndButtons() #Create the extremes
        self.createRemaining() #Create all other controllers
        #self.createExtra()

        window2.resize(625,625)
        self.window.show()


       
    def getMayaWindow(self):
        pointer = mui.MQtUtil.mainWindow()
        return shiboken2.wrapInstance(int(pointer), QtWidgets.QWidget)

    def createSelection(self,joint,hier,clear,button):
        add = False
        maya.cmds.select(str(joint),hierarchy=hier,add=add)
        button.setStyleSheet('background-color: white;')
        self.resetButtonclrs(button)


    def resetButtonclrs(self,ignoreButton):
        index = 0
        for button in self.button_list:
            color = self.button_clr_list[index]
            if button == ignoreButton:
                continue
            button.setStyleSheet("background-color :" + color+";")
            index += 1
        
    
    def createSelectionMultiple(self,j_list,prefix):
        maya.cmds.select(clear=True)
        for j in j_list:
            if j.find(prefix) != -1:
                maya.cmds.select(str(j),add=True)
    
    
    def connectButton(self,button,slot,hier=False,clear = True):
        button.clicked.connect(lambda: self.createSelection(slot,hier,clear,button))
        #self.changeButtonclr()
        self.button_fn_list.append(slot)
        button.setToolTip(slot)
        self.selected = button
        

    def connectButtonMultiple(self,button,slot,prefix):
        button.clicked.connect(lambda: self.createSelectionMultiple(slot,prefix))
        self.ToSelect = 'none'


    def createButton(self,row,column,rspan,cspan, w,h,clr ='rgb(232,129,129)' ):
        button = QtWidgets.QPushButton()
        self.layout.addWidget(button,row,column,rspan,cspan,Qt.AlignCenter)
        button.setMinimumSize(w,h)
        button.setMaximumSize(w,h)
        button.setStyleSheet("QPushButton"
                                "{"
                                "background-color :" + clr+";"
                                "}"
                                "QPushButton::pressed"
                                "{"
                                "background-color : red;"
                                "}")
        self.button_clr_list.append(clr)
        self.button_list.append(button)
        return button

    def getSwitches(self):
        l = maya.cmds.ls(typ='nurbsCurve',visible=True)
        l2 = copy.deepcopy(l)
        for element in l2:
            #print(f'{element},{element.find("Fk")}')
            e = element.lower()
            if element.lower().find("switch") == -1:
                #print(element)
                l.remove(element)
        l2 = copy.deepcopy(l)
        return l
    
    def getControllers(self):
        l = maya.cmds.ls(typ='nurbsCurve',visible=True)
        l2 = copy.deepcopy(l)
        for element in l2:
            
            e = element.lower()
            if element.lower().find("fk") == -1 or e.find('finger')!=-1 or e[len(e)-1].isdigit()==True:
                #print(element)
                l.remove(element)
        l2 = copy.deepcopy(l)
        for i in range (len(l2)):
            #print(l[i])
            l[i] = l[i].replace('Shape','')
        #print(l)
        return l
    def getControllersOther(self):
        l = maya.cmds.ls(typ='nurbsCurve',visible=True)
        l2 = copy.deepcopy(l)
        for element in l2:
            
            e = element.lower()
            if element.lower().find("fk") != -1 or e.find('eye')!=-1 or e.find('finger')!=-1 or e.find('ik')!=-1 or e[len(e)-1].isdigit()==True or e.find('main')!=-1 or e.find('ctrl')==-1 or e.find('thumb')!=-1 or e.find('switch')!=-1 or e.find('root')!=-1 :
                #print(element)
                if e.find('spine')!=-1:
                    continue
                l.remove(element)
        l2 = copy.deepcopy(l)
        for i in range (len(l2)):
            #print(l[i])
            l[i] = l[i].replace('Shape','')

        #print(l)
        return l
    def contains_number(self,string):
        return any(char.isdigit() for char in string)
    def getRotLock(self,element):
        return (maya.cmds.getAttr(element+'.rotateX',lock=True) and maya.cmds.getAttr(element+'.rotateY',lock=True) and maya.cmds.getAttr(element+'.rotateZ',lock=True))

    def getControllersIK(self):
        l = maya.cmds.ls(typ='nurbsCurve',visible=True)
        l2 = copy.deepcopy(l)
        for element in l2:
            #print(f'{element},{element.find("Fk")}')
            e = element.lower()
            if element.lower().find("ik") == -1 or e.find('finger')!=-1 or e[len(e)-1].isdigit()==True or e.find('switch')!=-1:
                #print(element)
                l.remove(element)
        l2 = copy.deepcopy(l)
        for i in range (len(l2)):
            #print(l[i])
            l[i] = l[i].replace('Shape','')

        #print(l)
        return l
           
    def getPositions(self, controller):
        pos = maya.cmds.xform(controller, a = True, ws = True, t= True, q = True)
        pos = [round(i,1) for i in pos]
        return pos
    
    def getExtremes(self):
        ex_left = [0,0,0]
        ex_names = ['a','b','c','d']
        ex_right = [0,0,0]
        ex_top = [0,0,0]
        ex_bottom = [0,0,0]
        con_lis = self.controller_list + self.getControllersOther()
        print(con_lis)
        for con in con_lis:
            con_pos = self.getPositions(con)
            if con_pos[0] < ex_left[0]:
                ex_left = con_pos
                ex_names[0] = con
            elif con_pos[0] > ex_right[0]:
                ex_right = con_pos
                ex_names[1] = con
            if con_pos[1] <= ex_bottom[1]:
                ex_bottom = con_pos
                ex_names[2] = con
            elif con_pos[1] > ex_top[1]:
                ex_top = con_pos
                ex_names[3] = con
        self.listOfPos[0] = ex_left
        self.listOfPos[1] = ex_right
        #print(ex_names)
        return ex_left,ex_right,ex_bottom, ex_top,ex_names
    

    def createEndButtons(self):
        ex_left,ex_right,ex_bottom, ex_top, ex_names = self.getExtremes()
        #print(ex_left)
        h_dist = round((self.gridSize[1]-2*self.colOffset)/2)
        v_dist = self.gridSize[0] - 2*self.rowOffset
        row_offset = self.rowOffset
        col_offset = self.colOffset
        row_lextreme = round(abs(ex_top[1]- ex_left[1])/abs(ex_top[1])*v_dist)
        col_textreme = round(abs(ex_left[0]- ex_top[0])/abs(ex_left[0])*h_dist)+col_offset
        col_bextreme = round(abs(ex_left[0]- ex_bottom[0])/abs(ex_left[0])*h_dist)+col_offset
        button = self.createButton(row_offset+row_lextreme,col_offset,1,2,self.colMinWidth*2,self.rowMinHeight)#left
        self.connectButton(button,ex_names[0])
        button = self.createButton(row_offset+row_lextreme,self.gridSize[1]-col_offset,1,2,self.colMinWidth*2,self.rowMinHeight) #right
        self.connectButton(button,ex_names[1])
        self.listOfPosRL[0] = [row_offset+row_lextreme,col_offset]
        self.listOfPosRL[1] = [row_offset+row_lextreme,self.gridSize[1]-col_offset]

        return h_dist,v_dist
    
    def checkIfexists(self,bpos):
        for pos in self.listOfPos:
            if bpos[1] == pos[1] and (bpos[0]==pos[0]):
                return True
        return False

    def checkIfexistsRC(self,bpos):
        for pos in self.listOfPosRL:
            if bpos[1] == pos[1] and bpos[0]==pos[0]:
                return True
        return False
    def sgn(self,op):
        if op>0:
            return 1
        elif op<0:
            return -1
        else:
            return 0
    
    def createRemaining(self):
        con_lis = self.controller_list
        ex_left,ex_right,ex_bottom, ex_top, ex_names = self.getExtremes()
        h_dist,v_dist = self.createEndButtons()
        for con in con_lis:
            if (con in ex_names[0:2]) or (con in self.finger_list) or maya.cmds.listRelatives(con,c=True) == None:
                continue
            con_pos = self.getPositions(con)
            
            if len(self.listOfPos) == 0:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)
            elif self.checkIfexists(con_pos) == False:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)
            elif self.checkIfexists(con_pos) == True:
                #print(con)
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)+1
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)
            self.listOfPos.append(con_pos)
            self.listOfPosRL.append([row_extreme,col_extreme])
            
            button = self.createButton(self.rowOffset+row_extreme,col_extreme+self.colOffset,1,2,self.colMinWidth*2,self.rowMinHeight)
            self.connectButton(button,con)
    def createExtra(self):
        con_lis = self.getControllersOther()
        ex_left,ex_right,ex_bottom, ex_top, ex_names = self.getExtremes()
        h_dist,v_dist = self.createEndButtons()
        for con in con_lis:
            con_pos = self.getPositions(con)
            #print(con)
            if self.getRotLock(con) == True:
                continue
            if len(self.listOfPos) == 0:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)
            elif con.lower().find('clavicle')!=-1:
                print(con)
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)+self.sgn(con_pos[0])*2
            elif con.find('Foot_Pivot_Orient_CTRL')!=-1:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)+self.sgn(con_pos[0])*2
            elif self.checkIfexists(con_pos) == False:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)
            elif self.checkIfexists(con_pos) == True:
                row_extreme = round(abs(ex_top[1]- con_pos[1])/abs(ex_top[1])*v_dist)-1
                col_extreme = round(abs(ex_left[0]- con_pos[0])/abs(ex_left[0])*h_dist)

            self.listOfPos.append(con_pos)

            self.listOfPosRL.append([row_extreme,col_extreme])
            clr = 'rgb(0,129,129)'
            if con.lower().find("fk") != -1:
                clr = 'rgb(0,129,229)'
            button = self.createButton(self.rowOffset+row_extreme,col_extreme+self.colOffset,1,2,self.colMinWidth*2,self.rowMinHeight,clr = clr)
            self.connectButton(button,con)
            
    def createFingerButtons(self,prefix,row,col):
        button = self.createButton(row,col,1,2,layout,self.colMinWidth*2,self.rowMinHeight)
        self.connectButtonMultiple(button,self.finger_list,prefix)
    
aupoticky = Autopicker()




