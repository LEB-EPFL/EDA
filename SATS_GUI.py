from PyQt5.QtCore import Qt, pyqtSignal, QT_VERSION_STR, QTimer
from PyQt5.QtWidgets import QWidget, QSlider, QPushButton, QLabel,\
    QGridLayout, QFileDialog, QProgressBar, QGroupBox, QApplication
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QColor, QBrush, QPen, QMovie
import pyqtgraph as pg
from skimage import io
from QtImageViewer import QtImageViewer
from qimage2ndarray import array2qimage
import sys
import os
import time
import numpy as np

from nnIO import loadiSIMmetadata, loadElapsedTime, loadNNData
# Adjust for different screen sizes
QApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)


class RectItem(pg.GraphicsObject):
    def __init__(self, rect, color='#FFFFFF', parent=None):
        super().__init__(parent)
        self._rect = rect
        self.color = color
        self.picture = QtGui.QPicture()
        self._generate_picture()

    @property
    def rect(self):
        return self._rect

    def _generate_picture(self):
        painter = QtGui.QPainter(self.picture)
        painter.setPen(pg.mkPen(color=self.color))
        painter.setBrush(pg.mkBrush(color=self.color))
        painter.drawRect(self.rect)
        painter.end()

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class KeyPressWindow(pg.PlotWidget):
    sigKeyPress = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, ev):
        self.scene().keyPressEvent(ev)
        self.sigKeyPress.emit(ev)


class SATS_GUI(QWidget):

    frameChanged = pyqtSignal([], [int])

    def __init__(self, app):
        QWidget.__init__(self)

        self.folder = (
             'C:/Users/stepp/Documents/data_raw/SmartMito/' +
             'microM_test/cell_Int5s_30pc_488_50pc_561_5')
        # Windows for plotting
        self.Plot = KeyPressWindow()
        self.pI = self.Plot.plotItem
        self.frames = self.pI.plot([])

        # Add second y axis
        self.p2 = pg.ViewBox()
        self.pI.showAxis('right')
        self.pI.scene().addItem(self.p2)
        self.pI.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.pI)

        self.pI.vb.sigResized.connect(self.updateViews)
        self.Plot.sigKeyPress.connect(self.incrementView)

        self.nnPlotItem = pg.PlotCurveItem([], pen='w')
        self.nnframes = pg.ScatterPlotItem([], symbol='o', pen=None)
        self.p2.setZValue(100)
        self.p2.addItem(self.nnPlotItem)
        self.p2.addItem(self.nnframes)

        self.frameratePlot = self.Plot.plot([])
        pen = pg.mkPen(color='#FF0000', style=Qt.DashLine)
        self.thrLine = pg.InfiniteLine(pos=100, angle=0, pen=pen)
        self.thrLine.hide()
        self.Plot.addItem(self.thrLine)

        self.scatter = pg.ScatterPlotItem()
        self.scatter.setData(brush='#505050', size=8, pen=None)
        self.Plot.addItem(self.scatter)

        # adapt for presentation
        labelStyle = {'color': '#AAAAAA', 'font-size': '20pt'}
        self.Plot.setLabel('right', 'Frame', **labelStyle)
        self.Plot.setLabel('bottom', 'Time [s]', **labelStyle)
        self.Plot.setLabel('left', 'NN output', **labelStyle)
        font = QtGui.QFont()
        font.setPixelSize(20)
        self.Plot.getAxis("bottom").setStyle(tickFont=font, tickTextHeight=500)
        self.Plot.getAxis("left").setStyle(tickFont=font)
        self.Plot.getAxis("right").setStyle(tickFont=font)

        # Place these windows into the GUI
        grid = QGridLayout(self)
        grid.addWidget(self.Plot, 0, 0)
        # grid.addWidget(self.Plot2, 1, 0)

        self.inc = 0
        self.app = app
        self.loadData()
        self.app.processEvents()
        self.updatePlot()

    def loadData(self):
        self.elapsed = loadElapsedTime(self.folder)
        self.elapsed = np.array(self.elapsed[0::2])/1000
        self.delay = loadiSIMmetadata(self.folder)
        self.nnData = loadNNData(self.folder)

    def updatePlot(self):
        if self.inc == 0:
            self.frames.setData(self.elapsed, np.zeros(len(self.elapsed)), symbol='o', pen=None)
            self.pI.getAxis('left').hide()

        elif self.inc == 1:
            self.nnPlotItem.setData(x=self.elapsed, y=np.arange(0, len(self.elapsed)))

        elif self.inc == 2:
            self.delay = np.append(np.ones(5), self.delay)
            rect_data = self.delay[0:len(self.elapsed)]
            # see where the delay value changes
            changes = np.where(np.roll(rect_data, 1) != rect_data)[0]
            # map this frame data to the elapsed time data
            changes = self.elapsed[changes]
            for i in range(1, len(changes)):
                color = '#202020' if i % 2 else '#101010'
                rect_item = RectItem(QtCore.QRectF(
                    changes[i-1], 0, changes[i]-changes[i-1], 200), color)
                self.Plot.addItem(rect_item)
                rect_item.setZValue(-100)

        elif self.inc == 3:
            self.nnPlotItem.hide()
            self.frames.hide()
            self.nnframes.setData(self.elapsed, np.zeros(len(self.elapsed)))
            # self.p2.setZValue(-1)
            self.pI.getAxis('right').hide()
            self.pI.getAxis('left').show()
            self.updateViews()

        elif self.inc == 4:
            # self.Plot.plot(self.elapsed, self.delay[0:len(self.elapsed)]*150)
            self.nnframes = ((self.nnData[:, 0] - 1) / 2).astype(np.uint16)
            self.nntimes = self.elapsed[self.nnframes]
            pen = pg.mkPen(color='#303030')
            self.Plot.plot(self.nntimes, self.nnData[:, 1], pen=pen)
            self.scatter.setData(self.nntimes, self.nnData[:, 1])

        elif self.inc == 5:
            self.thrLine.show()

        self.Plot.update()

    def updateViews(self):
        # view has resized; update auxiliary views to match
        self.p2.setGeometry(self.pI.vb.sceneBoundingRect())
        print('updateViews run')
        # need to re-update linked axes since this was called
        # incorrectly while views had different shapes.
        # (probably this should be handled in ViewBox.resizeEvent)
        self.p2.linkedViewChanged(self.pI.vb, self.p2.XAxis)

    def incrementView(self, event):
        if event.key() == 65:
            self.inc = self.inc + 1
            print(self.inc)
        self.updatePlot()


QtCore.QRectF()

app = QApplication(sys.argv)
gui = SATS_GUI(app)

gui.show()

sys.exit(app.exec_())