# -*- coding: utf-8 -*-
#pylint : disable=E0401
"""
@author: SUSHANT KEDAR				
DATACORE SOFTWARE PVT LTD CONFIDENTIAL
THIS SPEC IS THE PROPERTY OF DATACORE SOFTWARE PVT LTD.IT SHALL NOT BE
COPIED, USED,TRANSLATED OR TRANSFERRED IN WHOLE OR IN PART TO ANY THIRD
PARTY WITHOUT PRIOR WRITTEN PERMISSION OF DATACORE SOFTWARE PVT LTD.
File Name	:	run_vdbench.py
Description	:	This script is main script which validate pre-requesites.

"""
import os
import argparse
import time
from os import path
import sys
import datetime
sys.path.insert(0, os.path.abspath("../../../Lib/VdBenchLib"))
from execution import Test_ILDC
from error_log import LogCreat
from configparser import ConfigParser
sys.path.insert(0, os.path.abspath("../../../Pacakges"))
from autologin import AutoLoggin
import os.path
class Run():
    '''
    This method main run script.
    Arguments : None
    Return: None
    '''
    def __init__(self):
        self.config_file = r"../../../Config/VdBench_config/VDBench_config.ini"
        self.config_test = r"../../../Config/Test.txt"
        self.list_lines = []
        self.file  = ''
        configur = ConfigParser()
        configur.read(self.config_file)
        flag = 1
        msg = ''
        if configur.get('first run', 'run') == 'False':
            
            today = datetime.datetime.now()
            date_time = today.strftime("%y-%m-%d_%H-%M-%S")
            self.set_config_val('first run', 'start', date_time)
            flag, msg = AutoLoggin().run()
        print(flag, msg)
        if flag ==1 and msg == '':
            flag_ = self.verification_file()
            if flag_ == 0:
                self.arguments()
            else:
                Test_ILDC().start()
                self.set_config_val('first run', 'run', 'True')
                print('System will restart in 30 sec')
                time.sleep(30)
                os.system("shutdown /r /t 1")
        else:
            print(msg)
            LogCreat().logger_error.error(msg)
    def remove_test_file(self):
        if path.exists(self.config_test) is True:
            os.remove(self.config_test)
        path_ = os.path.abspath("")+'/'+"VdBench.bat"
        if path.exists(path_) is True:
            os.remove(path_)
    def set_config_val(self, section, key , val):
        configur = ConfigParser()
        configur.read(self.config_file)
        configur.set(section, key , val)
        with open(self.config_file, 'w') as configfile:
            configur.write(configfile)
    def config_creation(self, args):
        '''
        This method read user args and create hidden config for
        workload execution.
        Arguments (obj): args
        Return: None
        '''
        load = args.workload
        disk = args.disktype
        all_disk = ['ILDC','ILC','ILD','STANDARD']
        all_load = ['VDI', 'VSI', 'ORACLE', 'SQL']
        self.list_lines = []
        if disk.lower().strip() == 'all' and load.lower().strip() == 'all':
            for _ in all_disk:
                for j in all_load:
                    str_ = _.upper()+ ' '+ j.upper()
                    self.list_lines.append(str_)
        elif disk.lower().strip() == 'all' and load.lower().strip() != 'all':
            for _ in all_disk:
                str_ = _.upper()+ ' '+ load.upper()
                self.list_lines.append(str_)
        elif disk.lower().strip() != 'all' and load.lower().strip() == 'all':
            for _ in all_load:
                str_ = disk.upper()+ ' '+ _.upper()
                self.list_lines.append(str_)
        else:
            str_ = disk.upper()+' '+load.upper()
            self.list_lines.append(str_)
        with open(self.config_test, "w") as file:
            for item in self.list_lines:
                file.write("%s\n" % item)
            file.close()
    def verification_file(self):
        '''
        This method verify hidden config present or not.
        Arguments : None
        Return: None
        '''
        if path.exists(self.config_test) is True:
            self.file = open(self.config_test, "r+")
            data = self.file.readlines()
            self.file.close()
            if all(v == '\n' for v in data) is True:
                flag = 0
            else:
                flag = 1
        else:
            flag = 0
        return flag
    def arguments(self):
        '''
        This method take user inputs.
        Arguments : None
        Return: None
        '''
        configur = ConfigParser()
        configur.read(self.config_file)
        my_parser = argparse.ArgumentParser(description='Execute VD bench workloads')
        # Add the arguments
        my_parser.add_argument('-workload', '-w',
                               type=str,
                               help='Specify the workload to be executed.'\
                                   'Valid Values are : vsi,vdi,oracle,sql,all')
        my_parser.add_argument('-disktype', '-d',
                               type=str,
                               help='Specify the disk to be executed. '\
                                   'Valid Values are : ildc,ild,ilc,ssy,all')
        args = my_parser.parse_args()
        if (args.workload is not None) and (args.disktype is not None):
            self.config_creation(args)
            Test_ILDC().start()
            file = open(self.config_test, "r+")
            data = file.readlines()
            file.close()
            if data != []:
                self.set_config_val('first run', 'run', 'True')
            else:
                print('here')
                self.set_config_val('first run', 'run', 'False')
                self.set_config_val('first run', 'start', 'None')
                AutoLoggin().del_sub_sheduler()
                self.remove_test_file()
                # AutoLoggin().delete_reg_cmd()
            print('System will restart in 30 sec')
            time.sleep(30)
            os.system("shutdown /r /t 1")
        else:
            print('Invalid args are passed')
            self.set_config_val('first run', 'run', 'False')
            self.set_config_val('first run', 'start', 'None')
            AutoLoggin().del_sub_sheduler()
            self.remove_test_file()
            print('arg over')
if __name__ == "__main__":
    Run()


