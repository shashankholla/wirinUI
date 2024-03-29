import sys
#import PPG_Modules
import csvwriter 
from PyQt5.QtWidgets import *
import serial 
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.animation as anim 
from functools import partial 
import glob 
import threading
import wirinECGx
import pandas as pd

from csvwriter import *
import datetime
import pyOpenBCI
from multiprocessing import Process, Queue
from pyOpenBCI import OpenBCICyton
openBCIStream = []

buttonAction = "None"
board = None
q = Queue()

running = False
currentComPort = None
baudRate = 9600
graphInterval = 10
buffer = []
data = []
ix = 0

y1 = []
y2 = []
y3 = []
y4 = []
y5 = []
y6 = []
y7 = []
y8 = []
xss = []
data = []

bx = 0

BCIplt = plt.figure()
bciSub = BCIplt.add_subplot(1,1,1)


def annotator(button):
    global buttonAction
    if button.isChecked():
        buttonAction = button.text()

def print_raw(sample):
    global openBCIStream
    openBCIStream =  (sample.channels_data)
    #print("From print_Raw: ", end= "")
    #print(openBCIStream)
    
    q.put(openBCIStream)




   


def start_read():
    global running
    global buffer
    global buttonAction
    global board 
    #print("start reading")
    ser = serial.Serial(currentComPort, baudRate)
    running = True
    try:
        board = OpenBCICyton(port=None, daisy=False)
    except:
        print("Couldnt find OpenBCI")

    
    if(running):
        boardThread = threading.Thread(target=board.start_stream, args=(print_raw,))
        boardThread.daemon = True
        boardThread.start()

    while(running):

        data = ser.readline()
        data = data.decode().strip()
        systime = datetime.datetime.now().isoformat()
        #data = data + c 
        inp = filewriter(data,"newFile",buttonAction,systime)
        #print("inp is")
        #print(inp)
        n = len(inp)
        if len(buffer) > n:
            buffer = buffer[n:]
        buffer = buffer + inp
        #print(buffer)
    

t1 = threading.Thread(target=start_read, args=()) 

def findComPorts(menu):
    print("COM port detected")
    menu = menu
    menu.clear()
    #print("Hello")
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    #print(ports)
    #print(menu)
    for port in ports:
        
        try:
            s = serial.Serial(port)
            s.close()
            #print(type(port))
            result.append(port)
            
        except (OSError, serial.SerialException):
            pass
     
    
    #result = ["COM1","COM2"]
    if len(result) == 0:
        action = menu.addAction("NO PORTS")
        action.setEnabled(False)
    for r in result:
        r = menu.addAction(r)
    #menu.triggered.disconnect()
    #menu.triggered.connect(partial(setComPort, menu))

def setComPort(menu,a):
    global currentComPort
    #print(a.text())
    currentComPort = a.text()
    #print(currentComPort)
    label.setText("Com Port : " + currentComPort)
    findComPorts(menu)

def display(a):
    global running
    global t1
    global start

    case = a.text()
    print(currentComPort)
    if case == "Start":
        print("START")
        if(currentComPort == None):
            QMessageBox.warning(mainWindow, 'Error', "Choose COM Port", QMessageBox.Ok , QMessageBox.Ok)
        
        else:
        
            try:
        
                s = serial.Serial(currentComPort)
                s.close()

                start.setEnabled(False) 
                stop.setEnabled(True)
        
        
                ecgAnimate._start()
                ppgAnimate._start()
                respAnimate._start()       
        
        
                t1.start()
                
            except (OSError, serial.SerialException):
                QMessageBox.warning(mainWindow, 'Error', "COM Port not available \n Choose another one", QMessageBox.Ok , QMessageBox.Ok)
            
            
    elif case == "Stop":
        
        stop.setEnabled(False)
        start.setEnabled(True)
        running = False
        stop_read()

    elif case == "Plot":
        plot_data()
    elif case == "OpenBCI Plot":
        startBciProcess()        

    

def stop_read():
    global t1
    global board
    print("Stop")
    if(board != None):
        board.stop_stream()
    ecgAnimate.event_source.stop()
    ppgAnimate.event_source.stop()
    #ser.close()
    if(t1.isAlive()):
        t1.join()
        
        t1 = threading.Thread(target=start_read, args=()) 
    

def plot_data():
    print("plot")


def updateGraph():
    print("Update Graph")

#This function handles top menu bar press

def animateECG(i):
    global buffer
    #print("Inside animate")
    #pullData = open("eegdata.txt","r").read()
    #dataList = pullData.split('\n')
    
    x = (pd.read_csv(r"data_1.csv",header=None)[1][:4000]).tolist()
    m = wirinECGx.f(data,500.0)
    """ for eachLine in dataList:
        if len(eachLine)>1:
            x,y = eachLine.split(',')
            xList.append(int(x))
            yList.append(int(y)) """
    ecg.clear()
    if(len(m[2])):
        ecg.plot(m[1],m[2])


def animatePPG(i):
    #print("Inside animate")
    # pullData = open("eegdata.txt","r").read()
    # dataList = pullData.split('\n')
    # xList = []
    # yList = []
    # for eachLine in dataList:
    #     if len(eachLine)>1:
    #         x,y = eachLine.split(',')
    #         xList.append(int(x))
    #         yList.append(int(y))
    # ppg.clear()
    # ppg.plot(xList,yList)
    pass


def animateBCI(q,i):
    openBCIStream = []
    global ix
    global bx
    uVolts_per_count = (4500000)/24/(2**23-1)
    #print(type(q))
    
    for i in range(250):    
        if(not q.empty()):
            openBCIStream = q.get()
            
            
            try:
                #print("From animate =>", end="")
                #print(openBCIStream)
                y1.append(openBCIStream[0]*uVolts_per_count)
                # y2.append(openBCIStream[1]*uVolts_per_count)
                # y3.append(openBCIStream[2]*uVolts_per_count)
                # y4.append(openBCIStream[3]*uVolts_per_count)
                # y5.append(openBCIStream[4]*uVolts_per_count)
                # y6.append(openBCIStream[5]*uVolts_per_count)
                # y7.append(openBCIStream[6]*uVolts_per_count)
                # y8.append(openBCIStream[7]*uVolts_per_count) 
                xss.append(ix)
                ix += 1
                xs = xss[-50:]
            except:
                pass

        bciSub.clear()
        bciSub.plot(xs, y1[-50:])
        # bciSub.plot(xs, y2[-50:])
        # bciSub.plot(xs, y3[-50:])
        # bciSub.plot(xs, y4[-50:])
        # bciSub.plot(xs, y5[-50:])
        # bciSub.plot(xs, y6[-50:])
        # bciSub.plot(xs, y7[-50:])
        # bciSub.plot(xs, y8[-50:]) 
        


def startBciProcess():
    
    p = Process(target=bciPlotFunc, args=(q,))
    p.start()
    

def bciPlotFunc(q):
    global BCIplt
    global bciSub
    a = q.get()
    #print("In bciPlotFunc")
    #print(a)
    ani = anim.FuncAnimation(BCIplt, partial(animateBCI,q), interval=1000)
    plt.show()

def myExitHandler():
    stop_read()
    board.disconnect()
    
if __name__ == '__main__':    
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(myExitHandler)
    mainWindow = QMainWindow()
    mainWindow.setGeometry(50, 50, 500, 500)
    mainWindow.setWindowTitle("Readings")

    wid = QWidget()
    mainWindow.setCentralWidget(wid)
    hmainBox = QHBoxLayout()
    wid.setLayout(hmainBox)




    toolbar = QToolBar()
    mainWindow.addToolBar(toolbar)



    #Comports

    comPorts = QToolButton()
    toolbar.addWidget(comPorts)
    comPorts.setText("COM")

    #Comports list
    menu = QMenu()
    findComPorts(menu)
    menu.triggered.connect(partial(setComPort, menu))
    comPorts.setMenu(menu)
    comPorts.setPopupMode(QToolButton.InstantPopup)


    #Other toolbar buttons
    start = QAction(QIcon(),"Start", mainWindow)
    toolbar.addAction(start)
    stop  = QAction(QIcon(),"Stop", mainWindow)
    stop.setEnabled(False)
    toolbar.addAction(stop)
    plot  = QAction(QIcon(),"Plot", mainWindow)
    toolbar.addAction(plot)
    bciPlot  = QAction(QIcon(),"OpenBCI Plot", mainWindow)
    toolbar.addAction(bciPlot)
    toolbar.actionTriggered[QAction].connect(display)
    
    

    leftLayout = QVBoxLayout()
    leftLayout.setContentsMargins(0,0,0,0)
    leftLayout.setSpacing(0)
    ECGFigure = Figure()
    PPGFigure = Figure()
    ECGCanvas = FigureCanvas(ECGFigure)
    PPGCanvas = FigureCanvas(PPGFigure)

    

    ecg = ECGFigure.add_subplot(111)
    ecg.set_title("ECG")
    ppg = PPGFigure.add_subplot(111)
    ppg.set_title("PPG")
    ECGCanvas.draw()
    PPGCanvas.draw()
    ecgAnimate = anim.FuncAnimation(ECGFigure, animateECG, interval=graphInterval)
    ecgAnimate.event_source.stop()


    ppgAnimate = anim.FuncAnimation(PPGFigure, animatePPG, interval=graphInterval)
    ppgAnimate.event_source.stop()


    #canvas3.draw()
    ecgWindow = QWidget()
    ecgWindow.setContentsMargins(0,0,0,0)

    ecgWindow.setAutoFillBackground(True)
    ecgLayout = QVBoxLayout()
    ecgLayout.setContentsMargins(0,0,0,0)
    ecgLayout.setSpacing(0)
    ecgWindow.setLayout(ecgLayout)
    ppgWindow = QWidget()
    ppgLayout = QVBoxLayout()
    ppgLayout.setContentsMargins(0,0,0,0)
    ppgLayout.setSpacing(0)
    ppgWindow.setLayout(ppgLayout)

    ecgToolbar = NavigationToolbar(ECGCanvas,wid)
    ppgToolbar = NavigationToolbar(PPGCanvas,wid)

    plotSplitter = QSplitter(Qt.Vertical)
    ecgLayout.addWidget(ECGCanvas)
    ecgLayout.addWidget(ecgToolbar)

    leftLayout.addWidget(plotSplitter)
    ppgLayout.addWidget(PPGCanvas)
    ppgLayout.addWidget(ppgToolbar)
    plotSplitter.addWidget(ecgWindow)
    plotSplitter.addWidget(ppgWindow)
    plotSplitter.setSizes([400,400])
    plotSplitter.setStyleSheet("QSplitter::handle {   background: black;}")
    plotSplitter.setHandleWidth(1)

    leftWidget = QWidget()
    leftWidget.setLayout(leftLayout)

    horizontalSplitter = QSplitter(Qt.Horizontal)

    rightWidget = QWidget()

    rightSubLayout = QVBoxLayout()
    rightWidget.setLayout(rightSubLayout)

    btn1 = QRadioButton("Heavy Traffic", rightWidget)
    btn2 = QRadioButton("Moderate Traffic", rightWidget)
    btn3 = QRadioButton("Sparse Traffic", rightWidget)
    #btn4 = QRadioButton("something", rightWidget)
    #btn5 = QRadioButton("something else", rightWidget)
    btns = [btn1,btn2,btn3]
    x = []
    for btn in btns:
        rightSubLayout.addWidget(btn)

    btn1.toggled.connect(lambda:annotator(btn1))
    btn2.toggled.connect(lambda:annotator(btn2))
    btn3.toggled.connect(lambda:annotator(btn3))    
    title = QLabel()
    gsr = QLabel()
    heart_rate = QLabel()
    title.setText("Readings:")
    gsr.setText("GSR: {}".format(55))
    heart_rate.setText("Heart Rate: {}".format(72))
    title.setAlignment(Qt.AlignCenter)
    gsr.setAlignment(Qt.AlignRight)
    rightSubLayout.addWidget(title)
    rightSubLayout.addWidget(gsr)
    rightSubLayout.addWidget(heart_rate)

    horizontalSplitter.addWidget(leftWidget)
    horizontalSplitter.addWidget(rightWidget)
    horizontalSplitter.setSizes([500,200])

    horizontalSplitter.setStyleSheet("QSplitter::handle {   background: black;}")
    horizontalSplitter.setHandleWidth(1)
    hmainBox.addWidget(horizontalSplitter)

    hmainBox.setSpacing(0)
    hmainBox.setContentsMargins(0,0,0,0)

    statusBar = QStatusBar()
    mainWindow.setStatusBar(statusBar)
    label = QLabel()
    if currentComPort == None:
        label.setText("No COM Port Selected")
    else:
        label.setText("Com Port : " + currentComPort)

    statusBar.addPermanentWidget(label)

    mainWindow.show()

    sys.exit(app.exec_())

