# -*- coding: utf-8 -*-
# Description:
# key:     virtual key created for configparser. Ex: line1, line2
# value:   represents a full line of the INP File. Each parameter must be splitted.
# section: INP headers. Ex: [SUBCATCHMENTS]
# id:      element ID

from _parse_adapter import *
from _consts import *
import sys
import re
from wadi_tools import *

class ParseSwmm:
    def __init__ (self, filename):
        self.filename = filename
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read_file(ConfParsAdapter(open(self.filename)))
        self.param_guide = None

    def change_width(self, id, value):
        self.change_parameter('SUBCATCHMENTS', id, 'width', value)

    def change_slope(self, id, value):
        self.change_parameter('SUBCATCHMENTS', id, 'slope', value)

    def change_cn (self, id, value):
        self.change_parameter('INFILTRATION', id, 'cn', value)

    def change_imperv(self, id, value):
        self.change_parameter('SUBCATCHMENTS', id, 'imperv', value)

    def change_n_imperv(self, id, value):
        self.change_parameter('SUBAREAS', id, 'n_imperv', value)

    def change_n_perv(self, id, value):
        self.change_parameter('SUBAREAS', id, 'n_perv', value)

    def change_s_imperv(self, id, value):
        self.change_parameter('SUBAREAS', id, 's_imperv', value)

    def change_s_perv(self, id, value):
        self.change_parameter('SUBAREAS', id, 's_perv', value)

    def change_pct_zero(self, id, value):
        self.change_parameter('SUBAREAS', id, 'pct_zero', value)

    def change_roughness(self, id, value):
        self.change_parameter('TRANSECTS', id, 'nLeft', value)
        self.change_parameter('TRANSECTS', id, 'nRight', value)
        self.change_parameter('TRANSECTS', id, 'nChannel', value)

    def set_param_guide(self, param_guide):
        self.param_guide = param_guide

    def update_parameters(self, individual):
        for (param, id, _ , _ ), gene in zip(self.param_guide, individual):
            self._update_parameter(param, id, gene)
        self.save_inp()

    def get_key_by_id (self, section, id):
        for key, value in self.get_values(section):
            if (value[0] != ';'):
                # if [TRANSECTS] just return the value (line)
                if (section != 'TRANSECTS'):
                    if (self.get_id_from_value(value) == id):
                        return key, value
                else:
                # otherwise, we have to parse the file
                    if self.get_id_from_value(value) == 'NC':
                        nc_value = value
                        nc_key = key
                    if self.get_id_from_value(value) == 'X1':
                        point = self.get_contents_from_value(value)
                        if point == id:
                            return nc_key, nc_value
        print ("Error: [{}] id: {} not found".format(section, id))
        sys.exit()

    def set_value(self, section, key, value):
        self.parser.set(section, key, value)

    # funcao que ajusta a linha
    def set_line_value (self, value, header):
        line = ''
        for just, v in zip(header.values(), value.values()):
            if type(v) is not str:
                if type(v) == float:
                    v = '{0:.3f}'.format(v)
                v = str(v)
            line += v.ljust(just)
        return line

    # funcoes que separam cada valor da linha de um valor
    def parse_section(self, value, header):
        section_value = OrderedDict()
        split_values = value.split()
        for h, param in zip(header.keys(), split_values):
            section_value[h] = param
        return section_value

    def get_headers_from_section(self, section):
        if section == 'SUBCATCHMENTS':
            header = subcatchments_header
        if section == 'SUBAREAS':
            header = subareas_header
        if section == 'CONDUITS':
            header = conduits_header
        if section == 'INFILTRATION':
            header = infiltration_header
        if section == 'TRANSECTS':
            header = transects_header
        return header

    # retorna uma lista com os nomes das sections
    def get_sections(self):
        return self.parser.sections()

    # retorna uma lista com todos os valores da section especificada
    def get_values(self, section):
        return self.parser.items(section)

    # # extrai o valor do id de um value
    def get_id_from_value(self, value):
        #return re.split(r'\s+', value.rstrip('\s'))
        return value.split()[0].strip()
    #
    def get_contents_from_value(self, value):
        return value.split()[1].strip()

    # pega todas as IDs de uma section
    def get_id_list(self,section):
        id_list = []
        for key, value in self.get_values(section):
            if (value[0] != ';'): # ignora se for comentario
                id_list.append(self.get_id_from_value(value))
        return id_list

    def get_parameters_by_id(self, section, id, parameter):
        key, value = self.get_key_by_id (section, id)
        header = self.get_headers_from_section(section)
        section_value = self.parse_section(value, header)
        return key, header, section_value, section_value[parameter]

    def change_parameter(self, section, id, parameter, param_value):
        key, header, section_value, original_value = self.get_parameters_by_id(section, id, parameter)
        section_value[parameter] = param_value
        value = self.set_line_value(section_value, header)
        self.parser.set(section, key, value)

    # save the inp file
    def save_inp(self):
        inp_file = open (self.filename, 'w')
        for section in self.get_sections():
            inp_file.write('[{}]\n'.format(section))
            values = self.get_values(section)
            for value in values:
                inp_file.write(value[value_idx] + '\n')
            inp_file.write('\n')
        inp_file.close()

    # This part of the code isn't so elegant.
    def _update_parameter(self, param, id, value):
        if param == 'WIDTH':
            self.change_width(id, value)
        elif param == 'SLOPE':
            self.change_slope(id, value)
        elif param == 'CN':
            self.change_cn(id, value)
        elif param == 'IMPERVIOUS':
            self.change_imperv(id, value)
        elif param == 'N_PERV':
            self.change_n_perv(id, value)
        elif param == 'N_IMPERV':
            self.change_n_imperv(id, value)
        elif param == 'S_PERV':
            self.change_s_perv(id, value)
        elif param == 'S_IMPERV':
            self.change_s_imperv(id, value)
        elif param == 'PCT_ZERO':
            self.change_pct_zero(id, value)
        elif param == 'ROUGHNESS':
            self.change_roughness(id, value)

# def main():
#     # open swmm file
#     saocarlos = ParseSwmm('models/modelo.INP')
#
#     saocarlos.change_roughness('Ponto1', 666)
#     saocarlos.change_roughness('Ponto1', 666)
#     saocarlos.change_roughness('Ponto10', 666)
#     saocarlos.change_roughness('Ponto9', 666)
#     # saocarlos.change_cn('21', 123)
#     # saocarlos.change_imperv('2', 999)
#     # saocarlos.change_width('2', 888)
#     # saocarlos.change_slope('2', 777)
#     # saocarlos.change_n_imperv('2', 0.05)
#     # saocarlos.change_n_perv('2', 0.04)
#     # saocarlos.change_s_imperv('2', 0.03)
#     # saocarlos.change_s_perv('2', 0.02)
#     # saocarlos.change_pct_zero('2', 0.01)
#     # saocarlos.change_roughness('L-1', 0.123)
#
#     # save modifications
#     saocarlos.save_inp()
#
# if __name__ == '__main__':
#     main()
