# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 13:07:49 2023

@author: haya.monawwar
"""

from andes.core import (Algeb, Lag, LeadLagLimit, NumParam, Washout)
import math
from TCSCbase import TCSCBaseData, TCSCBase

class TCSCData(TCSCBaseData):
    def __init__(self):
        super().__init__()
        self.Kw = NumParam(info='Regulator gain ',
                          tex_name='K_w',
                          default=0.05,
                          unit='p.u.',
                          ipower=True,
                          )

        self.T1 = NumParam(info='Low-pass time constant',
                           default=0.1,
                           tex_name='T_1')
        self.T2 = NumParam(info='Lead time constant',
                           default=0.2,
                           tex_name='T_2')
        self.T3 = NumParam(info='Lag time constant',
                           default=10.0,
                           tex_name='T_3')
        self.Tw = NumParam(info='Washout time constant',
                           default=10.0,
                           tex_name='T_w')
        
        self.Kx = Algeb(info= 'Constant to calculate reactance of TCSC at a firing angle',
                        tex_name = 'K{x}',
                        e_str = 'math.sqrt(Xc/Xl)'
                        )
        
        self.R = Algeb(info = 'Reactance of TCSC', tex_name = 'X_TCSC{\u03B1}',
                       e_str = '[Xc * math.cos(Kx*(math.pi - alpha) \
                           * [(math.pi() * pow (Kx,4) - math.pi - 2*pow(Kx,4) \
                               *alpha + 2*pow(Kx,2)*alpha - math.sin(2*alpha)*pow(Kx,4) \
                            + math.sin(2*alpha)*pow(Kx,2) - \
                            4*pow(Kx,3)*pow(math.cos(alpha),2)*math.sin(math.pi() - alpha)\
                            - 4*pow(Kx,2)*math.cos(alpha)*math.sin(alpha) ))] ] / \
                              [math.pi * (pow(Kx,4) - 2*pow(Kx,2) + 1) \
                             * math.cos (Kx * (math.pi - alpha))]'

                       )

        self.alphaL = NumParam(info='Maximum firing angle',
                            tex_name='{\u03B1}max',
                            default=0.0,
                            unit='p.u.',
                            )
        self.alphaU = NumParam(info='Minimum firing angle',
                            tex_name='{\u03B1}min',
                            default=0.0,
                            unit='p.u.',
                            )


class TCSC1Model(TCSCBase):
    """
    Implement TCSC1 model.
    """

    def __init__(self, system, config):
        TCSCBase.__init__(self, system, config)

        self.pref = Algeb(info='Reference power input',
                          tex_name='P_{ref}',
                          v_str='Pref',  # How to initialize this? 
                          e_str='pref0 * K - pref',
                          )
        
        self.pbus = Algeb(info='Power at bus h',  # How to initialize this? 
                          tex_name='P_{h}',
                          fault=0.0,
                          unit='p.u.',
                          )
        
        self.u = Algeb(info='Power at washout block input',
                              tex_name='Pref - P_{h}',
                              e_str = 'Pref - P_{h} - u',
                              fault=0.0,
                              unit='p.u.',
                              )


        self.Washout = Washout(u=self.u, 
                               K=' Kw * Tw',
                               T=self.Tw,
                               tex_name = 'x1'
                               )
        
        self.Lag = Lag(u=self.Washout_y,
                          T1=self.T1,
                          K = 1, D=1,
                          tex_name = 'x2'
                          )
        
        self.LL = Lag(u=self.Lag_y,
                          T2=self.T2,
                          T3=self.T3,
                          K = 1,
                          lower = self.alphaL,
                          upper = self.alphaU,
                          tex_name = 'x3'
                          )
        
        
        self.output = Algeb(info= 'Final Output', tex_name = 'b{\u03B1}',
                            e_str= '1/self.R - b{\u03B1}')