# -*- coding: utf-8 -*-
from deap import base
from deap import creator
from deap import tools
from parse_options import *
from parse_swmm import *
from swmm_tools import *
from _consts import *
import uuid
import json
import importlib
import subprocess
import tempfile
import os
import sys
import shutil
import random
import csv
import pprint
import datetime

class Calibration:
    def __init__ (self, configfile, copy_files = True):
        self.ini_file = ParseSetup(configfile, copy_files)
        self.model_dir = self.ini_file.get_model_dir()
        self.result_dir = self.ini_file.get_result_dir()
        self.objective_function = self.ini_file.get_objective_function()
        self.data_filename = self.ini_file.get_field_data_filename()
        #self.nash_list = 'nash_list.csv'
        self.nash_list = self.ini_file.get_nse_results_filename() # save each evaluated nse
        self.random_seed = self.ini_file.get_random_seed_flag()
        # we are making a list of the best nash
        # best_nash[0] = global nash
        # best_nash[1] = dict with the nashes
        self.best_nash = [None, None]

        #self.param_list = 'param_list.csv'
        self.param_list = self.ini_file.get_param_results_filename() # save each evaluated param
        self.show_preprocessing_files = self.ini_file.get_show_preprocessing_files_flag()

        #self.gen_nash_list = 'gen_nse_results.csv'
        self.gen_nash_list = self.ini_file.get_gen_nse_results_filename() # save best nse of the generation

        self.ignore_penality = self.ini_file.get_ignore_penality_flag()
        self.show_summary = self.ini_file.get_show_summary_flag()

        #self.gen_param_list = 'gen_param_results.csv'
        self.gen_param_list = self.ini_file.get_gen_param_results_filename() # save best param of the generation

        self.save_evaluations_flag = self.ini_file.get_save_evaluations_flag()
        self.show_evaluations_flag = self.ini_file.get_show_evaluations_flag()
        self.show_penality_flag = self.ini_file.get_show_penality_flag()
        self.cn_groups = self.ini_file.get_cn_groups()
        self.impervious_groups = self.ini_file.get_impervious_groups()
#        self.n_perv_groups = self.ini_file.get_n_perv_groups()
#        self.n_imperv_groups = self.ini_file.get_n_imperv_groups()
#        self.s_perv_groups = self.ini_file.get_s_perv_groups()
#        self.s_imperv_groups = self.ini_file.get_s_imperv_groups()
#        self.pct_zero_groups = self.ini_file.get_pct_zero_groups()
        self.roughness_groups = self.ini_file.get_roughness_groups()
        self.param_guide = self.ini_file.get_all_parameters()
        self.previousError = minus_inf
        self.repeatCounter = 0
        self.nash_dict = None
        self.temp_inp = None
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        self.toolbox = base.Toolbox()
        self.setup_ga()
        self.remove_old_results()
        if self.save_evaluations_flag:
            self.save_individuals_convergence_header(self.param_list)
            self.save_individuals_convergence_header(self.gen_param_list)

    def remove_old_results(self):
        if self.show_preprocessing_files:
            print('Removing old files...')
        if os.path.exists(self.nash_list):
            os.remove(self.nash_list)
        if os.path.exists(self.param_list):
            os.remove(self.param_list)
        if os.path.exists(self.gen_nash_list):
            os.remove(self.gen_nash_list)
        if os.path.exists(self.gen_param_list):
            os.remove(self.gen_param_list)
        for inp_file in glob.glob(join(self.result_dir, 'wdtmp*')):
            os.remove(inp_file)
        if self.show_preprocessing_files:
            print(' - Done!')

    def feasible(self, individual):
        if self.ignore_penality:
            return True
        for v, lim in zip(individual, self.param_guide):
            if not lim[3] > v > lim[2]:
                return False
        return True

    def distance(self, individual):
        error_count = 0
        for v, lim in zip(individual, self.param_guide):
            if not lim[3] > v > lim[2]:
                error_count += 1
        if self.show_penality_flag:
            print('Infeasible solution penalty: ', error_count)
        return error_count

    def save_individuals_convergence_header(self, filename):
        param_header = []
        id_header = []
        values = self.ini_file.get_all_parameters()
        for value in values:
            param_header.append(value[0])
            id_header.append(value[1])
        with open(filename, "w") as output:
            wr = csv.writer(output, quoting=csv.QUOTE_ALL)
            wr.writerow(id_header)
            wr.writerow(param_header)

    # this method saves the current parameters to disk
    def save_individuals_convergence(self, individual, filename):
        with open(filename, "a") as output:
            wr = csv.writer(output, quoting=csv.QUOTE_ALL)
            wr.writerow(individual)

    def create_individual(self):
        individual_list = []
        values = self.ini_file.get_all_parameters()
        # tuple value (parameter, id, min, max)
        # we only want a random value between min and max
        for value in values:
            individual_list.append(random.uniform(float(value[2]), float(value[3])))
        return individual_list

    def setup_ga(self):
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self.create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self.fitness)
        self.toolbox.decorate("evaluate", tools.DeltaPenality (self.feasible, minus_inf, self.distance))
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        self.toolbox.register("select", tools.selTournament, tournsize=4)

    def clone_random_inp(self):
        inpfile = self.ini_file.get_inp_filename()
        tmpstr = 'wdtmp'+uuid.uuid4().hex
        tmpfile = join(self.result_dir, tmpstr+ '.inp')
        shutil.copyfile(inpfile, tmpfile)
        return tmpstr

    # evaluation function
    def fitness(self, individual):
        cwd = os.getcwd()
        self.temp_inp = self.clone_random_inp()
        os.chdir(self.result_dir)
        model = ParseSwmm(self.temp_inp + '.inp')
        model.set_param_guide (self.param_guide)

        # change swmm parameters
        model.update_parameters(individual)

        # running
        network = SwmmTools(model.filename, join(self.data_filename))

        # compute deviation
        nse, self.nash_dict, negative_count = network.calc_nash(self.objective_function)

        # nash geral menos a qtde de nash negativo em cada no
        if self.objective_function not in ['fo1', 'fo2', 'fo3']:
            print('O.F. {} is not defined.'.format(self.objective_function))

        if self.best_nash[0] == None or self.best_nash[0] < nse:
            self.best_nash[0] = nse
            self.best_nash[1] = self.nash_dict

        # saving nse to file
        if self.save_evaluations_flag:
            # save individuals to convergence file
            self.save_individuals_convergence(individual, self.param_list)
            # save each evaluated nash
            self.save_nash_list(self.nash_dict, self.nash_list);
        os.chdir(cwd)
        os.remove(join(self.result_dir,self.temp_inp+'.inp'))
        if self.show_evaluations_flag:
            self.show_evaluations(self.objective_function, nse, self.nash_dict, negative_count)
        return nse,

    def show_evaluations(self, objective_function, nse, nash_list, negative_count):
        color = Fore.RED
        if negative_count <= 0:
            color = Fore.GREEN
        output_str =  '{0}: {1:.2f}\nNc: {2}{3}{4}'.format(self.objective_function, nse, color, negative_count, Style.RESET_ALL)
        print("------------------------------------")
        print(output_str)
        pprint.pprint(nash_list)

    def save_nash_list(self, nash_dict, filename, best = False):
        if best and self.best_nash[0] != None:
            nash_dict = self.best_nash[1]
            print('      -- * * * --')
            print('Best OF: {}'.format(self.best_nash[0]))
            pprint.pprint(self.best_nash[1])
        if self.show_evaluations_flag:
            print('Saving in {}{}{}:'.format(Fore.CYAN,filename, Style.RESET_ALL))
            pprint.pprint(nash_dict)
        with open(filename, "a") as errors:
            nl = ','.join(str(e) for e in nash_dict.values())
            errors.write(nl+'\n')

    # save the best result
    def save_best(self, filename, individual):
        best = ParseSwmm(filename)
        best.set_param_guide(self.param_guide)
        best.update_parameters(individual)

    def calibrate(self):
        if not self.random_seed:
            random.seed(0)
        pop = self.toolbox.population(n=self.ini_file.get_n_pop())
        cx_prob = self.ini_file.get_crossover_prob()
        mut_prob = self.ini_file.get_mutation_prob()
        ngen = self.ini_file.get_n_gen()

        fitnesses = list(map(self.toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        print("Evaluated {} individuals".format(len(pop)))

        for g in range(ngen):
            self.best_nash = [None, None]
            print("=========================")
            print_bright("Generation {}".format(g))

            # choose the next generation
            offspring = self.toolbox.select(pop, len(pop))

            # clone selected individuals
            offspring = list(map(self.toolbox.clone, offspring))

            # compute the crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < cx_prob:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # compute the mutation
            for mutant in offspring:
                if random.random() < mut_prob:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # evaluate invalid individuals
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            print("Evaluated {} individuals".format (len(invalid_ind)))

            # offsprint complete replacement strategy
            pop[:] = offspring
            fits = [ind.fitness.values[0] for ind in pop]
            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x*x for x in fits)
            std = abs(sum2 / length - mean**2)**0.5
            nse = max(fits)
            if self.show_summary:
                print("  Min %s" % min(fits))
                print("  Max %s" % max(fits))
                print("  Avg %s" % mean)
                print("  Std %s" % std)
            #stop criteria:
            # when |f(x_i) - f(x_{i-1})|/f(x_i) stops decreasing
            #during n generations.
            #  n = 3.
            # if abs((nse - self.previousError)/nse) < 0.0000001:
            #     self.repeatCounter += 1
            # else:
            #     self.repeatCounter = 0
            # self.previousError = nse
            # if self.repeatCounter == 10:
            #     break
            #saving the best result at each generation
            best_ind = tools.selBest(pop, 1, fit_attr='fitness')[0]
            self.save_best(join(self.result_dir, self.ini_file.partial_filename), best_ind)
            self.save_individuals_convergence(best_ind, self.gen_param_list)
            self.save_nash_list(self.nash_dict, self.gen_nash_list, best = True)

        best_ind = tools.selBest(pop, 1)[0]
        self.save_best(join(self.result_dir, self.ini_file.final_filename), best_ind)

def get_nash(swmm_filename, spreadsheet_name, folder, fo='fo1'):
    model = SwmmTools(swmm_filename, spreadsheet_name, working_dir = folder, temp_file = False)
    nash, dict, nc = model.calc_nash(fo)
    print('nash: ' + str(nash))
    print('dict: ' + str(dict))

def show_instructions():
    print('Use:')
    print('  $ python3 calibration.py ')
    print('  $ python3 calibration.py -nse')

def main():
    param_file = 'saocarlos.ini'
    if len(sys.argv) > 3:
        show_instructions()
        sys.exit()

    if len(sys.argv) == 2:
        network = Calibration(param_file, copy_files = False)
        get_nash(network.ini_file.partial_filename, network.data_filename, network.result_dir, 'fo1')
        sys.exit()

    if len(sys.argv) == 3:
        network = Calibration(param_file, copy_files = False)
        get_nash(network.ini_file.partial_filename, network.data_filename, network.result_dir, sys.argv[2])
        sys.exit()

    start_time = datetime.datetime.now()

    print('Starting calibration. Start time: ', start_time);
    print('Please wait...')
    network = Calibration(param_file)
    network.calibrate()
    end_time = datetime.datetime.now()
    print ('Finished! Elapsed time: ', end_time - start_time)

if __name__ == '__main__':
    main()
