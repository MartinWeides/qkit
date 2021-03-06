# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2016
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import json
import pyqtgraph as pg
from qkit.storage.hdf_constants import ds_types

def _display_1D_view(self,graphicsView):
    ds = self.ds
    overlay_num = ds.attrs.get("overlays",0)
    overlay_urls = []
    x_axis = []
    y_axis = []
    for i in range(overlay_num+1):
        ov = ds.attrs.get("xy_"+str(i),"")
        ax = ds.attrs.get("xy_"+str(i)+"_axis","0:0")
        if ov:
            overlay_urls.append(ov.split(":"))
            x_a, y_a = ax.split(":")
            #print x_a, y_a
            x_axis.append(int(x_a))
            y_axis.append(int(y_a))
    ds_xs = []
    ds_ys = []
    for xy in overlay_urls:
        ds_xs.append(self.obj_parent.h5file[xy[0]])
        ds_ys.append(self.obj_parent.h5file[xy[1]])

    ds_x_url = ds.attrs.get("x_ds_url","")
    ds_y_url = ds.attrs.get("y_ds_url","")

    if ds_x_url and ds_y_url:
        ds_xs.append(self.obj_parent.h5file[ds_x_url])
        ds_ys.append(self.obj_parent.h5file[ds_y_url])

    graphicsView.clear()

    if not graphicsView.plotItem.legend:
        graphicsView.plotItem.addLegend(size=(160,48),offset=(30,15))

    for i, x_ds in enumerate(ds_xs):
        y_ds = ds_ys[i]
        # this is a litte clumsy, but for the cases tested it works well
        # should be changed to the ds_type-diffenentiation
        if len(x_ds.shape) == 1 and len(y_ds.shape) == 1:
            self.TraceSelector.setEnabled(False)
            x_data = np.array(x_ds)
            y_data = np.array(y_ds)

        elif len(x_ds.shape) == 2 and len(y_ds.shape) == 2:
            self.TraceSelector.setEnabled(True)
            range_max = np.minimum( x_ds.shape[0],y_ds.shape[0])
            self.TraceSelector.setRange(-1*range_max,range_max-1)

            x_data = np.array(x_ds[self.TraceNum])
            y_data = np.array(y_ds[self.TraceNum])

        elif len(x_ds.shape) == 1 and len(y_ds.shape) == 2:
            self.TraceSelector.setEnabled(True)
            range_max = y_ds.shape[0]
            self.TraceSelector.setRange(-1*range_max,range_max-1)

            x_data = np.array(x_ds)#,axis=x_axis[i])
            y_data = np.array(y_ds[self.TraceNum])#y_axis[i])#,axis=y_axis[i])

        else:
            return

        x_name = x_ds.attrs.get("name","_none_")
        y_name = y_ds.attrs.get("name","_none_")

        x_unit = x_ds.attrs.get("unit","_none_")
        y_unit = y_ds.attrs.get("unit","_none_")

        graphicsView.setLabel('left', y_name, units=y_unit)
        graphicsView.setLabel('bottom', x_name , units=x_unit)
        
        
        view_params = json.loads(ds.attrs.get("view_params",{}))
        
        # this allows to set a couple of plot related settings
        if view_params:
            aspect = view_params.pop('aspect',False)
            if aspect:
                graphicsView.setAspectLocked(lock=True,ratio=aspect)
            #bgcolor = view_params.pop('bgcolor',False)
            #if bgcolor:
            #    print tuple(bgcolor)
            #    graphicsView.setBackgroundColor(tuple(bgcolor))
                
        try:
            graphicsView.plotItem.legend.removeItem(y_name)
        except:
            pass

        # set the y data  to the decibel scale 
        if self.plot_scale == self.plot_scales['dB']:
            y_data = 10 *np.log10(y_data)
            graphicsView.setLabel('left', y_name, units="dB") 
        
        if self.plot_style==self.plot_styles['line']:
            graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite')
        if self.plot_style==self.plot_styles['linepoint']:
            symbols=['+','o','s','t','d']
            graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite',symbol=symbols[i%len(symbols)])
        if self.plot_style==self.plot_styles['point']:
            symbols=['+','o','s','d','t']
            graphicsView.plot(y=y_data, x=x_data, name = y_name,pen=None,symbol=symbols[i%len(symbols)])
            
    
    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()

    self._last_x_pos = 0
    
    def mouseMoved(mpos):
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()
            self.PointX.setText("X: %.6e"%(xval)) 
            self.PointY.setText("Y: %.6e"%(yval))
            
            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass
                
            self._last_x_pos = xval
    
    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_1D_data(self,graphicsView):
    ds = self.ds
    name = ds.attrs.get("name","_none_")
    unit = ds.attrs.get("unit","_none_")
    y_data = np.array(ds)

    if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
        x0 = ds.attrs.get("y0",ds.attrs.get("x0",0))
        dx = ds.attrs.get("dy",ds.attrs.get("dx",1))
        x_name = ds.attrs.get("x_name","_none_")
        x_unit = ds.attrs.get("x_unit","_none_")

        x_data = [x0+dx*i for i in xrange(y_data.shape[0])]

        #only one entry in ds, line style does not make any sense
        if self.ds.shape[0]==1:
            self.plot_style = self.plot_styles['point']

    elif self.ds_type == ds_types['matrix'] or (self.ds_type == -1 and len(self.ds.shape) == 2): #last expresson is for old hdf-files
        #x-dim in plot is y-dim in matrix dataset
        x0 = ds.attrs.get("y0",ds.attrs.get("x0",0))
        dx = ds.attrs.get("dy",ds.attrs.get("dx",1))
        x_name = ds.attrs.get("y_name","_none_")
        x_unit = ds.attrs.get("y_unit","_none_")

        if self.TraceValueChanged:
            #calc trace number from entered value
            num = int((self._trace_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
            self.TraceNum = num
            self.TraceSelector.setValue(self.TraceNum)
            self.TraceValueChanged = False

        x_data = [x0+dx*i for i in xrange(y_data.shape[1])]
        y_data = y_data[self.TraceNum]

        self.TraceValue.setText(self._getXValueFromTraceNum(ds,self.TraceNum))

        #only one y-entry in ds, line style does not make any sense
        if self.ds.shape[1]==1:
            self.plot_style = self.plot_styles['point']

    elif self.ds_type == ds_types['box']:
        #x-dim in plot is z-dim in box-dataset
        x0 = ds.attrs.get('z0',0)
        dx = ds.attrs.get('dz',1)
        x_name = ds.attrs.get('z_name','_none_')
        x_unit = ds.attrs.get('z_unit','_none_')

        if self.TraceXValueChanged:
            #calc trace number from entered value
            num = int((self._traceX_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
            self.TraceXNum = num
            self.TraceXSelector.setValue(self.TraceXNum)
            self.TraceXValueChanged = False
        
        if self.TraceYValueChanged:
            #calc trace number from entered value
            num = int((self._traceY_value-ds.attrs.get("y0",0))/(ds.attrs.get("dy",1)))
            self.TraceYNum = num
            self.TraceYSelector.setValue(self.TraceYNum)
            self.TraceYValueChanged = False


        x_data = [x0+dx*i for i in range(y_data.shape[2])]
        y_data = y_data[self.TraceXNum,self.TraceYNum,:]

        self.TraceXValue.setText(self._getXValueFromTraceNum(ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(ds,self.TraceYNum))

        #only one z-entry in ds, line style does not make any sense
        if self.ds.shape[2]==1:
            self.plot_style = self.plot_styles['point']

    graphicsView.setLabel('left', name, units=unit)
    graphicsView.setLabel('bottom', x_name , units=x_unit)

    # set the y data  to the decibel scale 
    if self.plot_scale == self.plot_scales['dB']:
        y_data = 10 *np.log10(y_data)
        graphicsView.setLabel('left', name, units="dB")

    if self.plot_style==self.plot_styles['line']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite')
    if self.plot_style==self.plot_styles['linepoint']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite',symbol='+')
    if self.plot_style==self.plot_styles['point']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=None, symbol='+')

    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()

    self._last_x_pos = 0
    
    def mouseMoved(mpos):
        y_unit = unit #here, yval and y_unit is the displayed measurement data
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()

            self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
            self.PointY.setText("Y: %.6e %s"%(yval,y_unit)) 

            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass

            self._last_x_pos = xval

    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_2D_data(self,graphicsView):
    ds = self.ds
    name = ds.attrs.get("name","_none_")
    unit = ds.attrs.get("unit","_none_")

    data = ds[()]
    fill_x = ds.shape[0]
    fill_y = ds.shape[1]
    x0 = ds.attrs.get("x0",0)
    dx = ds.attrs.get("dx",1)
    y0 = ds.attrs.get("y0",0)
    dy = ds.attrs.get("dy",1)
    x_name = ds.attrs.get("x_name","_none_")
    x_unit = ds.attrs.get("x_unit","_none_")
    y_name = ds.attrs.get("y_name","_none_")
    y_unit = ds.attrs.get("y_unit","_none_")

    if self.ds_type == ds_types['box']:
        if self.PlotTypeSelector.currentIndex() == 0:
            if self.TraceZValueChanged:
                #calc trace number from entered value
                num = int((self._traceZ_value-ds.attrs.get("z0",0))/(ds.attrs.get("dz",1)))
                self.TraceZNum = num
                self.TraceZSelector.setValue(self.TraceZNum)
                self.TraceZValueChanged = False

            data = data[:,:,self.TraceZNum]
        if self.PlotTypeSelector.currentIndex() == 1:
            if self.TraceXValueChanged:
                #calc trace number from entered value
                num = int((self._traceX_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
                self.TraceXNum = num
                self.TraceXSelector.setValue(self.TraceXNum)
                self.TraceXValueChanged = False

            data = data[self.TraceXNum,:,:]
            fill_x = ds.shape[0]
            fill_y = ds.shape[2]
            x0 = ds.attrs.get("y0",0)
            dx = ds.attrs.get("dy",1)
            y0 = ds.attrs.get("z0",0)
            dy = ds.attrs.get("dz",1)
            x_name = ds.attrs.get("y_name","_none_")
            x_unit = ds.attrs.get("y_unit","_none_")
            y_name = ds.attrs.get("z_name","_none_")
            y_unit = ds.attrs.get("z_unit","_none_")

        if self.PlotTypeSelector.currentIndex() == 2:
            if self.TraceYValueChanged:
                #calc trace number from entered value
                num = int((self._traceY_value-ds.attrs.get("y0",0))/(ds.attrs.get("dy",1)))
                self.TraceYNum = num
                self.TraceYSelector.setValue(self.TraceYNum)
                self.TraceYValueChanged = False

            data = data[:,self.TraceYNum,:]
            fill_x = ds.shape[1]
            fill_y = ds.shape[2]
            x0 = ds.attrs.get("x0",0)
            dx = ds.attrs.get("dx",1)
            y0 = ds.attrs.get("z0",0)
            dy = ds.attrs.get("dz",1)
            x_name = ds.attrs.get("x_name","_none_")
            x_unit = ds.attrs.get("x_unit","_none_")
            y_name = ds.attrs.get("z_name","_none_")
            y_unit = ds.attrs.get("z_unit","_none_")

        self.TraceXValue.setText(self._getXValueFromTraceNum(ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(ds,self.TraceYNum))
        self.TraceZValue.setText(self._getZValueFromTraceNum(ds,self.TraceZNum))

    xmin = x0
    xmax = x0+fill_x*dx
    ymin = y0
    ymax = y0+fill_y*dy

    pos = (xmin,ymin)

    graphicsView.clear()
    # scale is responsible for the "accidential" correct display of the axis
    # for downsweeps scale has negative values and extends the axis from the min values into the correct direction
    scale=((xmax-xmin)/float(fill_x),(ymax-ymin)/float(fill_y))
    graphicsView.view.setLabel('left', y_name, units=y_unit)
    graphicsView.view.setLabel('bottom', x_name, units=x_unit)
    graphicsView.view.setTitle(name+" ("+unit+")")
    graphicsView.view.invertY(False)
    
    graphicsView.setImage(data,pos=pos,scale=scale)
    graphicsView.show()

    # Fixme roi ...
    graphicsView.roi.setPos([xmin,ymin])
    graphicsView.roi.setSize([xmax-xmin,ymax-ymin])
    graphicsView.roi.setAcceptedMouseButtons(Qt.RightButton)
    graphicsView.roi.sigClicked.connect(lambda: self.clickRoi(graphicsView.roi.pos(), graphicsView.roi.size()))
    
    imIt = graphicsView.getImageItem()
    imVi = graphicsView.getView()
    
    def mouseMoved(mpos):
        z_unit = unit #here, zval and z_unit is the color coded measurement data
        mpos = mpos[0]
        if not self.obj_parent.liveCheckBox.isChecked():
            if imIt.sceneBoundingRect().contains(mpos):
                mousePoint = imIt.mapFromScene(mpos)
                x_index = int(mousePoint.x())
                y_index = int(mousePoint.y())
                if x_index > 0 and y_index > 0:
                    if x_index < fill_x and y_index < fill_y:
                        xval = x0+x_index*dx
                        yval = y0+y_index*dy
                        zval = data[x_index][y_index]
                        self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
                        self.PointY.setText("Y: %.6e %s"%(yval,y_unit)) 
                        self.PointZ.setText("Z: %.6e %s"%(zval,z_unit)) 
                        self.data_coord=  "%g\t%g\t%g" % (xval, yval,zval)

        else:
            xval = 0
            yval = 0
            zval = 0
            self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
            self.PointY.setText("Y: %.6e %s"%(yval,y_unit)) 
            self.PointZ.setText("Z: %.6e %s"%(zval,z_unit)) 
            self.data_coord=  "%g\t%g\t%g" % (xval, yval,zval)
    

    self.proxy = pg.SignalProxy(imVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)
    ################################
    #from guppy import hpy
    #h = hpy()
    #print h.heap()


def _display_table(self,graphicsView):
    #load the dataset:
    data = np.array(self.ds)
    if self.ds_type == ds_types['matrix']:
        data = data.transpose()
    if self.ds_type == ds_types['vector']:
        data_tmp = np.empty((1,data.shape[0]),dtype=np.float64)
        data_tmp[0] = data
        data = data_tmp.transpose()
    if self.ds_type == ds_types["txt"]:
        data_tmp = []
        for d in data:
            data_tmp.append([d])
        data = np.array(data_tmp)
        graphicsView.setFormat(unicode(data))
    graphicsView.setData(data)
    
def _display_text(self,graphicsView):
    data = np.array(self.ds)
    txt = ""
    for d in data:
        txt += d+'\n'
    graphicsView.insertPlainText(txt)
