# filename: Virtual_Coil.py
# Jochen Braumueller <jochen.braumueller@kit.edu>, 11/2013
# updates: 02/2015, 06/2016
# virtual coil instrument to be used as a wrapper for the DELFT tunnel electronics driver IVVI
# use: 
#  - set current range of downstream current source
#  - current unit is mA, independent of the specified and set range

# import and usage
"""
IVVI = qt.instruments.create('IVVI', 'IVVIDIG_main', address='COM6') #COM6 corresponds to adapter D in the UFO setup
vcoil = qt.instruments.create('vcoil', 'Virtual_Coil', dacs = [5])   #dacs to be used in list form [dac(ch1), dac(ch2), dac(ch3), ...]
vcoil.init()   #optional
vcoil.set_c_range('1m')
vcoil.set_current(1.0)
"""

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from instrument import Instrument
import instruments
import types
import logging
import numpy as np
import time
import os, sys
import qt

if 'IVVI' not in qt.instruments.get_instrument_names():
    logging.error('Instrument IVVI not found.')
    raise ImportError
else:
    IVVI = qt.instruments.get('IVVI')

DAC_ROUT = [5]   #dac port(s) to be used, passed as a list during instanciating
dac_val = {'20m':1.30103,'10m':1,'1m':0,'100u':-1,'10u':-2,'1u':-3,'100n':-4,'10n':-5,'1n':-6}   #DELFT electronics dictionary

class Virtual_Coil(Instrument):

    def __init__(self, name, dacs = DAC_ROUT, dacranges = None):
        """
        init virtual instrument object
        Inputs:
            - name: qt instrument name
            - dacs: list of routes of channels in use, e.g. [5] or [5,9,2]
            - dacranges: list of length len(dacs) indicating the dac ranges set at the device, list entries one of 'bi' for -2000,2000, 'pos' for 0,4000, 'neg' for -4000,0
        """
        Instrument.__init__(self, name, tags=['virtual'])
        
        self.dacs = dacs
        try:
            self.channels = len(self.dacs)
        except TypeError:
            logging.error('Error reading dac ports to be used. Import as list.')
        if dacranges == None:
            dacranges = ['bi']*self.channels
        else:
            if len(dacranges) != self.channels:
                logging.errors('dacranges not specified properly')
        limits_dict = {'bi':[-2000,2000],'pos':[0,4000],'neg':[-4000,0]}
        self.range_limits = [limits_dict[dacranges[i]] for i in range(self.channels)]
        #print self.range_limits
        if self.channels == 1:
            self.add_parameter('current', type=types.FloatType, flags=Instrument.FLAG_GETSET, units='mA')
            self.add_parameter('range', type=types.StringType, flags=Instrument.FLAG_GETSET)
        elif self.channels > 1 and self.channels <= 16:
            self.add_parameter('current', type=types.FloatType, flags=Instrument.FLAG_GETSET, units='mA', channels=(1, self.channels), channel_prefix='ch%d_')
            self.add_parameter('range', type=types.StringType, flags=Instrument.FLAG_GETSET, channels=(1, self.channels), channel_prefix='ch%d_')
        else:
            logging.error('incorrect number of channels specified')
        
        self.c_ranges = ['1m']*self.channels

    def do_set_range(self, range, channel = 1):
        """
        set the current range of channel ch
        """
        if range in dac_val:
            self.c_ranges[channel-1] = range
        else:
            logging.error('Invalid current range.')

    def do_get_range(self, channel = 1):
        """
        get the current range of channel ch
        """
        return self.c_ranges[channel-1]

    def do_set_current(self, current, channel = 1):   #current in mA
        """
        set current of channel ch
        """
        try:
            val = np.round(-0.5*(self.range_limits[channel-1][0]+self.range_limits[channel-1][-1])+(current * 1000 * np.power(10.,-dac_val[self.c_ranges[channel-1]])),10)   #dac value in mV
            #print val
            if val < -2000 or val > 2000:
                logging.error('Value exceeds threshold!')
                print 'dac range limits for this channel'
                raise ArithmeticError
            else:
                if 10.*val != np.round(10.*val):
                    logging.warning('16 bit resolution may be visible for the current value you are attempting to set.')
                IVVI.set_dac(self.dacs[channel-1],val)
                
        except IndexError as detail:
            logging.error('Electronics might be disconnected.')
            print detail
        except ArithmeticError as detail:
            logging.error('Invalid current setting. No changees made.')
            print detail
            
    def ramp_to(self, target = 0, ch = 1, steps = 100, dt = 0.05):
        """
        ramp current to target
        Inputs:
            - target: target current value
            - ch: channel index (1..)
            - steps: number of steps
            - dt: wait time between two steps
        """
        for c in np.linspace(self.do_get_current(ch),target,steps):
            self.do_set_current(c,ch)
            time.sleep(dt)
    
    def do_get_current(self, channel = 1):
        """
        get current of channel ch
        """
        val = float(IVVI.get_dac(self.dacs[channel-1]))/1000   #dac value in mV
        #print val
        try:
            return val * np.power(10.,dac_val[self.c_ranges[channel-1]])
        except IndexError as detail:
            logging.error('Electronics might be disconnected.')
            print detail
        except Exception as detail:
            logging.error(detail)
