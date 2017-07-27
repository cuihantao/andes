from numpy import ndarray, array, concatenate
from cvxopt import matrix
from . import dime


class Streaming(object):
    """Data streaming class for LTB"""
    def __init__(self, system):
        self.system = system
        self.dimec = dime.Dime(system.Settings.dime_name, system.Settings.dime_server)
        self.params_built = False

        _dicts = ['SysParam', 'Idxvgs', 'ModuleInfo']
        _lists = ['Varheader', 'last_devices']

        for item in _dicts:
            self.__dict__[item] = dict()
        for item in _lists:
            self.__dict__[item] = list()

        if self.system.Settings.dime_enable:
            try:
                self.dimec.start()
                self.system.Log.debug('DiME connection established.')
            except:
                self.dimec.exit()
                self.dimec.start()
                self.system.Log.debug('DiME connection established.')

    def _build_SysParam(self):
        if self.system.Bus.n:
            params = ['idx', 'Vn', 'voltage', 'angle', 'area', 'region']
            data_list = self._build_list('Bus', params)
            self.SysParam.update({'Bus': array(data_list).T})

        if self.system.PQ.n:
            params = ['bus', 'Sn', 'Vn', 'p', 'q', 'vmax', 'vmin', 1, 'u']
            data_list = self._build_list('PQ', params)
            self.SysParam.update({'PQ': array(data_list).T})

        if self.system.PV.n:
            params = ['bus', 'Sn', 'Vn', 'pg', 'v0', 'qmax', 'qmin', 'vmax', 'vmin', 0, 'u']
            data_list = self._build_list('PV', params)
            self.SysParam.update({'PV': array(data_list).T})

        if self.system.SW.n:
            params = ['bus', 'Sn', 'Vn', 'v0', 'a0', 'qmax', 'qmin', 'vmax', 'vmin', 'pg', 0, 1, 'u']
            data_list = self._build_list('SW', params)
            self.SysParam.update({'SW': array(data_list).T})

        if self.system.Shunt.n:
            params = ['bus', 'Sn', 'Vn', 'fn', 'g', 'b', 'u']
            data_list = self._build_list('Shunt', params)

            self.SysParam.update({'Shunt': array(data_list).T})

        if self.system.PMU.n:
            params = ['bus', 'Vn', 'fn', 'Tv', 'Ta', 'u']
            data_list = self._build_list('PMU', params)

            self.SysParam.update({'Pmu': array(data_list).T})

        if self.system.BusFreq.n:
            params = ['bus', 'Tf', 'Tw', 'u']
            data_list = self._build_list('BusFreq', params)

            self.SysParam.update({'Busfreq': array(data_list).T})

        if self.system.Syn2.n:
            syn_params = ['bus', 'Sn', 'Vn', 'fn', 2, 'xl', 'ra',
                          0, 'xd1', 0, 0, 0,
                          0, 0, 0, 0, 0,
                          'M', 'D', 0, 0,
                          'gammap', 'gammaq', 0,
                          0, 0, 'coi', 'u'
                          ]
            data_list2 = self._build_list('Syn2', syn_params)
            data_array2 = array(data_list2).T
        else:
            data_array2 = array([]).reshape(0, 28)

        if self.system.Syn6a.n:
            syn_params = ['bus', 'Sn', 'Vn', 60, 6, 'xl', 'ra',
                          'xd', 'xd1', 'xd2', 'Td10', 'Td20',
                          'xq', 'xq1', 'xq2', 'Tq10', 'Tq20',
                          'M', 'D', 0, 0,
                          'gammap', 'gammaq', 'Taa',
                          'S10', 'S12', 'coi', 'u']
            data_list6 = self._build_list('Syn6a', syn_params)
            data_array6 = array(data_list6).T
        else:
            data_array6 = array([]).reshape(0, 28)

        data_array = concatenate((data_array2, data_array6), axis=0)
        self.SysParam.update({'Syn': data_array})

        if self.system.AVR1.n or self.system.AVR2.n or self.system.AVR3.n:

            if self.system.AVR1.n:
                params = ['syn', 2, 'vrmax', 'vrmin', 'Ka', 'Ta', 'Kf', 'Tf', 'Ke', 'Te',
                          'Tr', 'Ae', 'Be', 'u']
                data_list_avr1 = self._build_list('AVR1', params)
                data_array_avr1 = array(data_list_avr1).T
            else:
                data_array_avr1 = array([]).reshape(0, 14)

            if self.system.AVR2.n:
                params = ['syn', 1, 'vrmax', 'vrmin', 'K0', 'T1', 'T2', 'T3', 'T4',
                          'Te', 'Tr', 'Ae', 'Be', 'u']
                data_list_avr2 = self._build_list('AVR2', params)
                data_array_avr2 = array(data_list_avr2).T
            else:
                data_array_avr2 = array([]).reshape(0, 14)

            if self.system.AVR3.n:
                params = ['syn', 3, 'vfmax', 'vfmin', 'K0', 'T2', 'T1', 1, 0, 'Te', 'Tr', 0, 0, 'u']
                data_list_avr3 = self._build_list('AVR3', params)
                data_array_avr3 = array(data_list_avr3).T

            else:
                data_array_avr3 = array([]).reshape(0, 14)

            data_array = concatenate((data_array_avr1, data_array_avr2, data_array_avr3), axis=0)
            self.SysParam.update({'Exc': data_array})

            # find bus of the Syn based on AVR.syn idx
            syn_bus = self.system.DevMan.get_param('Synchronous', param='bus', fkey=self.SysParam['Exc'][:, 0])
            # find position of the Syn based on Syn_bus
            self.SysParam['Exc'][:, 0] = self._find_pos('Syn', syn_bus)
            self.SysParam['Exc'][:, 0] += 1

        if self.system.TG1.n or self.system.TG2.n:
            if self.system.TG1.n:
                params = ['gen', 1, 'wref0', 'R', 'Tmax', 'Tmin', 'Ts', 'Tc', 'T3', 'T4', 'T5', 'u']
                data_list_tg1 = self._build_list('TG1', params)
                data_array_tg1 = array(data_list_tg1).T
            else:
                data_array_tg1 = array([]).reshape(0, 12)

            if self.system.TG2.n:
                params = ['syn', 2, 'wref0', 'R', 'pmax', 'pmin', 'T2', 'T1', 0, 0, 0, 'u']
                data_list_tg2 = self._build_list('TG2', params)
                data_array_tg2 = array(data_list_tg2).T
            else:
                data_array_tg2 = array([]).reshape(0, 12)

            data_array = concatenate((data_array_tg1, data_array_tg2), axis=0)
            self.SysParam.update({'Tg': data_array})

        if self.system.PSS1.n or self.system.PSS2.n:
            if self.system.PSS1.n:
                params = ['avr', 1, 'Ic1', 'vcu', 'vcl', 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
                data_list_pss1 = self._build_list('PSS1', params)
                data_array_pss1 = array(data_list_pss1).T
            else:
                data_array_pss1 = array([]).reshape(0, 23)

            if self.system.PSS2.n:
                params = ['avr', 2, 'Ic', 'vcu', 'vcl', 0, 0, 0, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
                data_list_pss2 = self._build_list('PSS2', params)
                data_array_pss2 = array(data_list_pss2).T
            else:
                data_array_pss2 = array([]).reshape(0, 23)

            data_array = concatenate((data_array_pss1, data_array_pss2), axis=0)
            self.SysParam.update({'Pss': data_array})

            avr_gen = self.system.DevMan.get_param('AVR', param='syn', fkey=self.SysParam['Pss'][:, 0])
            self.SysParam['Pss'][:, 0] = self._find_pos('Exc', avr_gen)
            self.SysParam['Pss'][:, 0] += 1

        if self.system.WTG3.n:
            params = ['bus', 'wind', 'Sn', 'Vn', 'fn', 'rs', 'xs', 'rr', 'xr', 'xmu', 'Hm',
                      'Kp', 'Tp', 'KV', 'Te', 'R', 'p', 'nblade', 'ngb', 'pmax', 'pmin', 'qmax', 'qmin', 'u']
            data_list = self._build_list('WTG3', params)
            self.SysParam.update({'Dfig': array(data_list).T})

    def _build_Varheader(self):
        self.Varheader = self.system.VarName.unamex + self.system.VarName.unamey

    def _build_Idxvgs(self):
        m = self.system.DAE.m
        n = self.system.DAE.n
        self.Idxvgs['System'] = {'nBus': self.system.Bus.n,
                                 'nLine': self.system.Line.n,
                                 }
        self.Idxvgs['Bus'] = {'theta': 1 + n + array(self.system.Bus.a),
                              'V': 1 + n + array(self.system.Bus.v),
                              'w_Busfreq': array(self.system.BusFreq.w),
                              'P': array([1]),
                              'Q': array([1]),
                              }
        self.Idxvgs['Line'] = {'Pij': array([1]),
                               'Pji': array([1]),
                               'Qij': array([1]),
                               'Qji': array([1]),
                               'Iij': array([1]),
                               'Iji': array([1]),
                               'Sij': array([1]),
                               'Sji': array([1]),
                               }
        self.Idxvgs['Syn'] = {'delta': array(self.system.Syn6a.delta),
                              'omega': array(self.system.Syn6a.omega),
                              'e1d': array(self.system.Syn6a.e1d),
                              'e1q': array(self.system.Syn6a.e1q),
                              'e2d': array(self.system.Syn6a.e2d),
                              'e2q': array(self.system.Syn6a.e2q),
                              'psid': array(self.system.Syn6a.psid),
                              'psiq': array(self.system.Syn6a.psiq),
                              'p': array(self.system.Syn6a.p),
                              'q': array(self.system.Syn6a.q),
                              }
        # self.Idxvgs['Tg'] = {'pm': array(self.system.TG1.pout + self.system.TG2.pout),
        #                      'wref': array(self.system.TG1.wref + self.system.TG2.wref),
        #                      }
        # self.Idxvgs['Exc'] = {'vf': array(self.system.AVR1.vfout + self.system.AVR2.vfout + self.system.AVR3.vfout),
        #                       'vm': array(self.system.AVR1.vm + self.system.AVR2.vm + self.system.AVR3.vm),
        #                       }
        # self.Idxvgs['Dfig'] = {'omega_m': array(self.system.WTG3.omega_m),
        #                        'theta_p': array(self.system.WTG3.theta_p),
        #                        'idr': array(self.system.WTG3.ird),
        #                        'iqr': array(self.system.WTG3.irq),
        #                        }

    def _build_list(self, model, params, ret=None):
        if not ret:
            ret = []
        else:
            ret = list(ret)

        for p in params:
            if type(p) in (int, float):
                ret.append([p] * len(ret[0]))
            elif type(p) == list:
                assert len(p) == len(ret[0])
                ret.append(p)
            else:
                ret.append(list(self.system.__dict__[model].__dict__[p]))

        return ret

    def _find_pos(self, model, fkey, src_col=0):
        """Find the positions of foreign keys in the source model index list"""
        if type(fkey) == ndarray:
            fkey = fkey.tolist()
        elif type(fkey) in (int, float):
            fkey = [fkey]

        ret = []
        model_idx_list = self.SysParam[model][:, src_col].tolist()
        for item in fkey:
            ret.append(model_idx_list.index(item) if item in model_idx_list else 0)

        return ret

    def build_init(self):
        """Build `Varheader`, `Idxvgs` and `SysParam` after power flow routine"""
        self._build_SysParam()
        self._build_Idxvgs()
        self._build_Varheader()

    def send_init(self, recepient='all'):
        """Broadcast `Varheader`, `Idxvgs` and `SysParam` to all DiME clients after power flow routine"""
        if not self.system.Settings.dime_enable:
            return
        if not self.params_built:
            self.build_init()
        if recepient == 'all':
            self.dimec.broadcast('Varheader', self.Varheader)
            self.dimec.broadcast('Idxvgs', self.Idxvgs)
            self.dimec.broadcast('SysParam', self.SysParam)
            self.system.Log.info('Varheader, Idxvgs and SysParam broadcasted.')
        else:
            if type(recepient) != list:
                recepient = [recepient]
            for item in recepient:
                self.dimec.send_var(item, 'Varheader', self.Varheader)
                self.dimec.send_var(item, 'Idxvgs', self.Idxvgs)
                self.dimec.send_var(item, 'SysParam', self.SysParam)

    def record_module_init(self, module_name, init_var):
        """Record the variable requests from modules"""
        if hasattr(self.ModuleInfo, module_name):
            self.ModuleInfo[module_name].update(init_var)
        else:
            self.ModuleInfo[module_name] = init_var

    def handle_event(self, Event):
        """Handle Fault, Breaker, Syn and Load Events"""
        pass

    def sync_and_handle(self):
        """Sync until the queue is empty"""
        if not self.system.Settings.dime_enable:
            return

        while True:
            var_name = self.dimec.sync()
            if not var_name:
                break

            current_devices = self.dimec.get_devices()
            workspace = self.dimec.workspace
            var_value = workspace[var_name]

            # send Varheader, SysParam and Idxvgs to modules on the fly
            if set(current_devices) != set(self.last_devices):
                new_devices = list(current_devices)
                for item in last_devices:
                    new_devices.remove(item)
                self.send_init(new_devices)

                self.last_devices = current_devices

            if var_name in current_devices:
                self.record_module_init(var_name, var_value)

            elif var_name == 'Event':
                self.handle_event(var_value)

            else:
                self.system.Log.warning('Synced variable {} not handled'.format(var_name))

    def vars_to_modules(self):
        """Stream the last results to the modules"""
        if not self.system.Settings.dime_enable:
            return

        for mod in self.ModuleInfo.keys():
            idx = self.ModuleInfo[mod]['varvgsidx']
            values = self.system.VarOut.vars[-1][idx]

            Varvgs = {'t': self.system.VarOut.t,
                      'k': self.system.VarOut.k,
                      'vars': values,
                      }

            self.dimec.send_var(mod, 'Varvgs', Varvgs)