# -*- coding: utf-8 -*-
import configparser
from _consts import _parameters_section_list
from deap import base
from parse_swmm import *
import numpy as np
from itertools import chain
import shutil
import glob
from wadi_tools import *

class ParseSetup:
    def __init__ (self, ini_filename, copy_files = True):
        self.ini_filename = ini_filename
        self.config = configparser.ConfigParser()
        self.config.read(self.ini_filename)
        self.model_dir = self.get_model_dir()
        self.result_dir = self.get_result_dir()
        self.inp_filename = self.get_inp_filename()
        self.partial_filename = self.get_partial_filename()
        self.final_filename = self.get_calibrated_filename()
        self.show_preprocessing_files = self.get_show_preprocessing_files_flag()
        self.model = ParseSwmm(self.inp_filename)
        self.wmin, self.wmax, self.smin, self.smax = self.get_global_limits()
        if copy_files:
            self.copy_files()

    def copy_files(self):
        try:
            if self.show_preprocessing_files:
                print('Copying rain files...')
            for file in glob.glob(join(self.model_dir,'*.DAT')):
                if self.show_preprocessing_files:
                    print(' - {}'.format(file)) # don't delete this line
                shutil.copy(file, self.result_dir)
        except Exception as e:
            print('Error copying rain files. '+str(e))
            sys.exit()
        try:
            shutil.copyfile(self.inp_filename, join(self.result_dir, self.partial_filename))
        except Exception as e:
            print('Error copying partial file.'+str(e))
            sys.exit()
        try:
            shutil.copyfile(self.inp_filename, join(self.result_dir, self.final_filename))
        except Exception as e:
            print('Error copying final file.'+str(e))
            sys.exit()

    def get_objective_function(self):
        return self.config.get('GA', 'objective_function')

    def get_model_dir(self):
        return self.config.get('SETUP', 'model_dir')

    def get_result_dir(self):
        return self.config.get('SETUP', 'result_dir')

    def get_data_dir(self):
        return self.config.get('SETUP', 'data_dir')

    def get_n_pop(self):
        return self.config.getint('GA', 'pop')

    def get_n_gen(self):
        return self.config.getint('GA', 'gen')

    def get_random_seed_flag(self):
        return self.config.getboolean('GA', 'random_seed')

    def get_crossover_prob(self):
        return self.config.getfloat('GA', 'cx_prob')

    def get_mutation_prob(self):
        return self.config.getfloat('GA', 'mut_prob')

    def get_inp_filename(self):
        return join(self.get_model_dir(), self.config.get('SETUP', 'inpfile'))

    def get_nse_results_filename(self):
        return self.config.get('SETUP', 'nse_results')

    def get_gen_nse_results_filename(self):
        return self.config.get('SETUP', 'gen_nse_results')

    def get_param_results_filename(self):
        return self.config.get('SETUP', 'param_results')

    def get_gen_param_results_filename(self):
        return self.config.get('SETUP', 'gen_param_results')

    def get_partial_filename(self):
        return self.config.get('SETUP', 'partial_file')
        #return join(self.get_result_dir(), self.config.get('SETUP', 'partial_file'))

    def get_calibrated_filename(self):
        return self.config.get('SETUP', 'calibrated_file')
        #return join(self.get_result_dir(), self.config.get('SETUP', 'calibrated_file'))

    def get_field_data_filename(self):
        return join(self.get_data_dir(), self.config.get('SETUP', 'field_data_file'))

    def get_save_evaluations_flag(self):
        return self.config.getboolean('DEBUG', 'save_evaluations')

    def get_show_evaluations_flag(self):
        return self.config.getboolean('DEBUG', 'show_evaluations')

    def get_show_preprocessing_files_flag(self):
        return self.config.getboolean('DEBUG', 'show_preprocessing_files')

    def get_show_penality_flag(self):
        return self.config.getboolean('DEBUG', 'show_penality')

    def get_show_summary_flag(self):
        return self.config.getboolean('DEBUG', 'show_summary')

    def get_ignore_penality_flag(self):
        return self.config.getboolean('DEBUG', 'ignore_penality')

    def get_cn_groups(self):
        return self.get_group_keys('CN')

    def get_impervious_groups(self):
        return self.get_group_keys('IMPERVIOUS')

    def get_n_perv_groups(self):
        return self.get_group_keys('N_PERV')

    def get_n_imperv_groups(self):
        return self.get_group_keys('N_IMPERV')

    def get_s_perv_groups(self):
        return self.get_group_keys('S_PERV')

    def get_s_imperv_groups(self):
        return self.get_group_keys('S_IMPERV')

    def get_pct_zero_groups(self):
        return self.get_group_keys('PCT_ZERO')

    def get_roughness_groups(self):
        return self.get_group_keys('ROUGHNESS')

    def get_global_limits(self):
        wmin = self.config.getfloat('GLOBAL_LIMITS', 'wmin')
        wmax = self.config.getfloat('GLOBAL_LIMITS', 'wmax')
        smin = self.config.getfloat('GLOBAL_LIMITS', 'smin')
        smax = self.config.getfloat('GLOBAL_LIMITS', 'smax')
        return wmin, wmax, smin, smax

    def calculate_global_intervals(self):
        section = 'SUBCATCHMENTS'
        id_list = self.model.get_id_list(section)
        width_list = np.array([],dtype=float)
        slope_list = np.array([],dtype=float)

        for id in id_list:
            # getting all widht values from INP, and storing in widht_list
            _, _, _, original_width = self.model.get_parameters_by_id(section, id, 'width')
            fwidth = float(original_width)
            width_list = np.append(width_list, fwidth)

            # gettint all slope values from INP
            _, _, _, original_slope = self.model.get_parameters_by_id(section, id, 'slope')
            fslope = float(original_slope)
            slope_list = np.append(slope_list, fslope)
        # compute the limits for widths and slopes
        width_list_min = width_list * (1 + self.wmin)
        width_list_max = width_list * (1 + self.wmax)
        slope_list_min = slope_list * (1 + self.smin)
        slope_list_max = slope_list * (1 + self.smax)

        return zip(['WIDTH']*len(width_list_min), id_list, width_list_min.tolist(), width_list_max.tolist()), zip(['SLOPE']*len(slope_list_min), id_list, slope_list_min.tolist(), slope_list_max.tolist())

    def get_group_keys(self, section):
        keys = []
        for (key, value) in self.config.items(section):
            keys.append(key)
        return keys

    def get_values_by_key(self, section, key):
        values = self.config[section][key].split(',')
        return values

    def get_all_local(self):
        parameters = []
        for group_section in _parameters_section_list:
            group_keys = self.get_group_keys (group_section + '_GROUP')
            for group_key in group_keys:
                id_list = self.get_values_by_key(group_section+'_GROUP', group_key)
                id_limits = self.get_values_by_key(group_section, group_key)
                for id in id_list:
                    parameters.append((group_section, id, float(id_limits[0]), float(id_limits[1])))
        return parameters

    def get_all_parameters(self):
        parameters = []
        width_list, slope_list = self.calculate_global_intervals()
        parameters.append(list(width_list))
#        parameters.append(list(slope_list))
        parameters.append(self.get_all_local())
        return list(chain.from_iterable(parameters))


#####################################################
# The code down below is used only for test purposes.
####################################################
# def main():
#     sanca = ParseSetup('saocarlos.ini')
#
#     # pega nome do arquivo do swmm
#     inpfile = sanca.get_inp_filename()
#     print('INP file: ' + inpfile)
#
#     # pega nome do arquivo com dados observados
#     datafile = sanca.get_field_data_filename()
#     print('Data file: ' + datafile)
#
#     # pega n populacao
#     n_pop = sanca.get_n_pop()
#     print('n pop: ' + str(n_pop))
#
#     # pega n populacao
#     n_gen = sanca.get_n_gen()
#     print('n gen: ' + str(n_gen))
#
#     # pega intervalo de busca de width
#     interval = sanca.get_global_limits()
#     print('global limits: '+ str(interval))
#
#     # pega nome dos grupos de determinada section
#     # no exemplo, pegamos todos os grupos da
#     # section IMPERVIOUS
#     grupos = sanca.get_group_keys('IMPERVIOUS')
#     print('Grupos: ' + str(grupos))
#
#     # pega os valores de determinada key
#     # de uma section especificada
#     # ex: pegar os IDs de um grupo chamado
#     # grupo1 grupos da section 'IMPERVIOUS'
#     Ids = sanca.get_values_by_key('N_PERV_GROUP', 'group1')
#     print('Ids: '+str(Ids))
#
#     # pega todos os parametros
#     list = sanca.get_all_parameters()
#     for v in list:
#         print(v)
#
# if __name__ == '__main__':
#     main()
