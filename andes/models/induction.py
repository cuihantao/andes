"""
Induction machine models
"""

#  [ANDES] (C)2015-2020 Hantao Cui
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  File name: induction.py
#  Last modified: 8/16/20, 7:25 PM

import logging
from andes.core.model import Model, ModelData  # NOQA
from andes.models.exciter import ExcQuadSat  # NOQA
from andes.core.param import IdxParam, NumParam, ExtParam  # NOQA
from andes.core.var import Algeb, State, ExtAlgeb  # NOQA
from andes.core.discrete import LessThan  # NOQA
from andes.core.service import ConstService, VarService, ExtService  # NOQA
from andes.core.service import InitChecker, FlagValue  # NOQA
import numpy as np  # NOQA

logger = logging.getLogger(__name__)


class IndBaseData(ModelData):
    """Base parameters for induction machines
    """
    def __init__(self):
        ModelData.__init__(self)
        self.bus = IdxParam(model='Bus',
                            info="interface bus id",
                            mandatory=True,
                            )

        self.Sn = NumParam(default=100.0,
                           info="Power rating",
                           tex_name='S_n',
                           )

        self.Vn = NumParam(default=110.0,
                           info="AC voltage rating",
                           tex_name='V_n',
                           )
        self.fn = NumParam(default=60.0,
                           info="rated frequency",
                           tex_name='f',
                           )

        self.rs = NumParam(default=0.01,
                           info="rotor resistance",
                           z=True,
                           tex_name='r_s',
                           non_zero=True,
                           )

        self.xs = NumParam(default=0.15,
                           info="rotor reactance",
                           z=True,
                           tex_name='x_s',
                           non_zero=True,
                           )
        self.rr1 = NumParam(default=0.05,
                            info="1st cage rotor resistance",
                            z=True,
                            non_zero=True,
                            tex_name='r_{R1}',
                            )
        self.xr1 = NumParam(default=0.15,
                            info="1st cage rotor reactance",
                            z=True,
                            tex_name='x_{R1}',
                            non_zero=True,
                            )
        self.rr2 = NumParam(default=0.001,
                            info="2st cage rotor resistance",
                            z=True,
                            non_zero=True,
                            tex_name='r_{R2}',
                            )
        self.xr2 = NumParam(default=0.04,
                            info="2st cage rotor reactance",
                            z=True,
                            tex_name='x_{R2}',
                            non_zero=True,
                            )

        self.xm = NumParam(default=5.0,
                           info="magnetization reactance",
                           z=True,
                           tex_name='x_m',
                           non_zero=True,
                           )

        self.Hm = NumParam(default=3.0,
                           info='Inertia constant',
                           power=True,
                           tex_name='H_m',
                           unit='kWs/KVA',
                           )

        self.c1 = NumParam(default=0.1,
                           info='1st coeff. of Tm(w)',
                           tex_name='c_1',
                           )

        self.c2 = NumParam(default=0.02,
                           info='2nd coeff. of Tm(w)',
                           tex_name='c_2',
                           )

        self.c3 = NumParam(default=0.02,
                           info='2nd coeff. of Tm(w)',
                           tex_name='c_3',
                           )

        self.ts = NumParam(default=1.0,
                           info='startup time',
                           tex_name='t_s',
                           )

        self.zb = NumParam(default=1.0,
                           info='Allow working as brake',
                           tex_name='z_b',
                           vrange=(0, 1),
                           )


class Ind5Model(Model):
    """
    Fifth-order Induction Machine equations.
    """

    def __init__(self, system, config):
        Model.__init__(self, system, config)

        self.flags.pflow = True
        self.flags.tds = True
        self.group = 'Induction'

        # services
        self.wb = ConstService(v_str='2 * pi * fn',
                               tex_name=r'\omega_b',
                               )
        self.x0 = ConstService(v_str='xs + xm',
                               tex_name='x_0',
                               )
        self.xp = ConstService(v_str='xs + xr1 * xm / (xr1 + xm)',
                               tex_name="x'",
                               )
        self.T10 = ConstService(v_str='(xr1 + xm) / (wb * rr1)',
                                tex_name="T'_0",
                                )
        self.xpp = ConstService(v_str='xs + xr1*xr2*xm / (xr1*xr2 + xr1*xm + xr2*xm)',
                                tex_name="x''",
                                )
        self.T20 = ConstService(v_str='(xr2 + xr1*xm / (xr1 + xm) ) / (wb * rr2)',
                                tex_name="T''_0",
                                )

        self.aa = ConstService(v_str='c1 + c2 + c3',
                               tex_name=r'\alpha',
                               )

        self.bb = ConstService(v_str='-c2 - 2 * c3',
                               tex_name=r'\beta',
                               )
        self.M = ConstService(v_str='2 * Hm',
                              tex_name='M',
                              )

        # network algebraic variables
        self.a = ExtAlgeb(model='Bus',
                          src='a',
                          indexer=self.bus,
                          tex_name=r'\theta',
                          info='Bus voltage phase angle',
                          e_str='u * (vd * Id + vq * Iq)'
                          )
        self.v = ExtAlgeb(model='Bus',
                          src='v',
                          indexer=self.bus,
                          tex_name=r'V',
                          info='Bus voltage magnitude',
                          e_str='u * (vq * Id - vd * Iq)'
                          )

        self.vd = Algeb(info='d-axis voltage',
                        e_str='-u * v * sin(a) - vd',
                        tex_name=r'V_d',
                        )

        self.vq = Algeb(info='q-axis voltage',
                        e_str='u * v * cos(a) - vq',
                        tex_name=r'V_q',
                        )

        self.slip = State(tex_name=r"\sigma",
                          e_str='u * (tm - te)',
                          t_const=self.M,
                          diag_eps=True,
                          )

        self.e1d = State(info='real part of 1st cage voltage',
                         e_str='u * (wb*slip*e1q - (e1d + (x0 + xp) * Iq)/T10)',
                         tex_name="e'_d",
                         )

        self.e1q = State(info='imaginary part of 1st cage voltage',
                         e_str='u * (-wb*slip*e1d - (e1q - (x0 - xp) * Id)/T10)',
                         tex_name="e'_q",
                         )

        self.e2d = State(info='real part of 2nd cage voltage',
                         e_str='u * '
                               '(-wb*slip*(e1q - e2q) + '
                               '(wb*slip*e1q - (e1d + (x0 + xp) * Iq)/T10) - '
                               '(e1d - e2q - (xp - xpp) * Iq)/T20)',
                         tex_name="e''_d",
                         diag_eps=True,
                         )
        self.e2q = State(info='imag part of 2nd cage voltage',
                         e_str='u * '
                               '(wb*slip*(e1d - e2d) + '
                               '(-wb*slip*e1d - (e1q - (x0 - xp) * Id)/T10) - '
                               '(e1q - e2d + (xp - xpp) * Id) / T20)',
                         tex_name="e''_q",
                         diag_eps=True,
                         )

        self.Id = Algeb(tex_name='I_d',
                        e_str='u * (vd - e2d - rs * Id + xpp * Iq)',
                        )

        self.Iq = Algeb(tex_name='I_q',
                        e_str='u * (vq - e2q - rs * Iq - xpp * Id)',
                        )

        self.te = Algeb(tex_name=r'\tau_e',
                        e_str='u * (e2d * Id + e2q * Iq) - te',
                        v_str='u * (e2d * Id + e2q * Iq)',
                        )

        self.tm = Algeb(tex_name=r'\tau_m',
                        e_str='u * (aa + bb * slip + c2 * slip * slip) - tm',
                        v_str='u * (aa + bb * slip + c2 * slip * slip)',
                        )


class Ind5(IndBaseData, Ind5Model):
    """
    Fifth-order induction machine model.

    See "Power System Modelling and Scripting" by F. Milano.
    """
    def __init__(self, system, config):
        IndBaseData.__init__(self)
        Ind5Model.__init__(self, system, config)