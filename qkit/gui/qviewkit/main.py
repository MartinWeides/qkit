# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2015
"""
import sys
from PyQt4 import QtCore
from PyQt4.QtCore import QObject,SIGNAL,SLOT,pyqtSignal
from PyQt4.QtGui import QApplication



import argparse

#import numpy as np
#import h5py

from PlotWindow import PlotWindow

class DATA(QObject):
    open_plots = {}
    open_ds    = {}
    dataset_info = {}
    ds_tree_items= {}
    ds_cmd_open = {}
    toBe_deleted = []

    "a set of housekeeping functions..."
        
    def append_plot(self,parent,window_id,ds):
        # self, item, dataset
        
        window = PlotWindow(parent,self,ds)
        self.open_plots[window_id]=window
        self.open_ds[ds]=window_id
        
        window.show()   # non-modal
        #window.exec_() # modal
        #window.raise_()
        
        return window
    def _toBe_deleted(self,ds):
        if self.open_ds.has_key(ds):
            self.toBe_deleted.append(ds)
    def _remove_plot_widgets(self, closeAll = False):
        def close_ds(ds):
            if self.open_ds.has_key(ds):
                item = self.open_ds[ds]
                item.setCheckState(0,QtCore.Qt.Unchecked)
                # make sure data is consitent                
                if self.open_plots.has_key(item):
                    self.open_plots.pop(item)
                if self.open_ds.has_key(ds):                
                    self.open_ds.pop(ds)

        if closeAll:
            for ds in self.open_ds.keys():
                close_ds(ds)
        else:
            for ds in self.toBe_deleted:
                close_ds(ds)
                
        self.toBe_deleted = []
            
    def remove_plot(self,window_id,ds):
        if self.open_plots.has_key(window_id):
            self.open_plots.pop(window_id)
        if self.open_ds.has_key(ds):
            self.open_ds.pop(ds)
    def plot_is_open(self,ds):
        #print ds, self.open_ds.has_key(ds)
        return self.open_ds.has_key(ds)
        
    def has_dataset(self,ds):
        return self.dataset_info.has_key(ds)
        
# Main entry to program.  
def main(argv):
    
    # some configuration boilerplate
    data = DATA()
    
    parser = argparse.ArgumentParser(
        description="Qviewkit / qkit tool to visualize qkit-hdf files // HR@KIT 2015")
    

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    
    parser.add_argument('-rt','--refresh_time', type=float, help='(optional) refresh time')
    parser.add_argument('-sp','--save_plot',  default=False,action='store_true', help='(optional) save default plots')
    parser.add_argument('-live','--live_plot',default=False,action='store_true', help='(optional) if set, plots are reloaded')    
    args=parser.parse_args()
    data.args = args
    

    # create Qt application
    app = QApplication(argv,True)
    
    # create main window
    from DatasetsWindow import DatasetsWindow
    #
    dsw = DatasetsWindow(data)
    dsw.show()
    dsw.raise_()
    
    # Connect signal for app finish
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    # Start the app up
    #sys.exit(app.exec_())
    app.exec_()
    #app.closeAllWindows()
 
if __name__ == "__main__":
    main(sys.argv)
