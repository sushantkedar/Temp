# -*- coding: utf-8 -*-
#pylint : disable=E0401
"""
@author: SUSHANT KEDAR				
DATACORE SOFTWARE PVT LTD CONFIDENTIAL
THIS SPEC IS THE PROPERTY OF DATACORE SOFTWARE PVT LTD.IT SHALL NOT BE
COPIED, USED,TRANSLATED OR TRANSFERRED IN WHOLE OR IN PART TO ANY THIRD
PARTY WITHOUT PRIOR WRITTEN PERMISSION OF DATACORE SOFTWARE PVT LTD.
File Name	:	test_file.py
Description	:	This script is going to call all Rest API of SSY
                as user want.

"""
import sys
import os
import json
import time
from configparser import ConfigParser
sys.path.insert(0, os.path.abspath("../../../Interface/REST"))
from ILDC import ILDC
from Disks import Disks
sys.path.insert(0, os.path.abspath("../../../Lib/VdBenchLib"))
from error_log import LogCreat
from vdbench import VdBenchRun

class Test_ILDC:
    '''
    This class read user input of disk and workload
    and execute VdBench tool.
    Arguments : None
    Return: None
    '''
    pool_id = ''
    vdbench_path = ''
    server_id = ''
    def __init__(self):
        self.pd_ids = []
        self.config_dict = {}
        self.disk = []
        self.file = ''
        self.flag = 0
        self.co_disk = []
        self.disk_pool_disk = []
        self.test_status = ''
        self.vd_id  = ''
    def start(self):
        '''
        This method execute the test.
        Arguments : None
        Return: None
        '''
        time.sleep(180)
        self.config_dict = {}
        self.get_host()
        self.get_server()
        flag = self.run()
        if flag == 0:
            self.execute_test()
    def get_physical_disk_id(self):
        '''
        This method used to get all physical disk details.
        Arguments : None
        Return: None
        '''
        uri = "physicaldisks"
        pd_data = Disks().do_get_physical_disks(uri, header=None)
        pd_data = json.loads(pd_data.content)
        if len(pd_data) != 0:
            self.pd_ids = {x['DiskIndex']:x["Id"] for x in pd_data if x['Partitioned'] == False}
            msg = "Found %d physical disks in server group" % len(self.pd_ids)
            LogCreat().logger_info.info(msg)
        else:
            msg = "No Physical disks found"
            LogCreat().logger_error.error(msg)
        return self.pd_ids
    def read_config(self):
        '''
        This method read configuration file of VdBench.
        Arguments : None
        Return: None
        '''
        configur = ConfigParser()
        configur.read(r"../../../Config/VdBench_config/VDBench_config.ini")
        self.config_dict['co disk'] = configur.get('Server level co', 's_disk').split(',')
        self.config_dict['diskpool_disk'] = configur.get('disk pool disk', 'd_disk').split(',')
        print(self.config_dict)
        self.disk = self.config_dict['co disk'] + self.config_dict['diskpool_disk']
        return self.disk
    def run(self):
        '''
        This method validate disk is used by othere process.
        If its used by othere process it will raise error and
        stop execution of tool.
        Arguments : None
        Return: None
        '''
        flag = 0
        self.read_config()
        pd_ids = self.get_physical_disk_id()
        for _ in self.disk:
            ILDC().clean_diskpart(_)
            if int(_) not in pd_ids.keys():
                msg = 'Disk index '+str(_)+ ' Already used by other process'
                print(msg)
                LogCreat().logger_error.error(msg)
                flag = 1
            else:
                if _ in self.config_dict['co disk']:
                    self.co_disk.append(pd_ids[int(_)])
                else:
                    self.disk_pool_disk.append(pd_ids[int(_)])
        del self.config_dict
        return flag
    def input_for_test(self):
        '''
        This method pass disk and workload details to the tool.
        Arguments : None
        Return: None
        '''
        flag_run  = 0
        vd_name = ''
        workload = ''
        self.file = open(r"../../../Config/Test.txt", "r+")
        data = self.file.readlines()
        self.file.close()
        if data == []:
            msg = 'There is nothing to perform plz give vdbench configuration'
            LogCreat().logger_info.info(msg)
        else:
            virtual_disk = data[0].split()
            vd_name = virtual_disk[0]
            workload = virtual_disk[1]
            flag_run = 1
            file = open(r"../../../Config/Test.txt", "w+")
            for _ in data[1:]:
                file.write(_)
            file.close()
        return vd_name, workload, flag_run
    def execute_test(self):
        '''
        This method execute workload and create all required
        configuration of SSY.
        Arguments : None
        Return: None
        '''
        vd_name, workload, flag_run  = self.input_for_test()
        if flag_run == 1:
            print('************************'\
                  'Test Started************************\n')
            LogCreat().logger_info.info('************************'\
                                        'Test Started************************')
            time.sleep(10)
            if vd_name.lower() != "standard":
                self.test_enable_cap_opt_at_server()
            time.sleep(15)
            self.create_diskpool(vd_name)
            time.sleep(15)
            self.stop_server()
            time.sleep(25)
            self.start_server()
            time.sleep(25)
            self.test_create_virtual_disk(vd_name)
            time.sleep(50)
            self.set_vd_properties(vd_name)
            time.sleep(5)
            self.test_serve_vd_to_host()
            time.sleep(10)
            diskindex = self.initialize_vd()
            time.sleep(5)
            print('************************'\
                  'VdBench Execution Started************************\n')
            LogCreat().logger_info.info('************************'\
                                        'VdBench Execution Started************************')
            VdBenchRun().run(vd_name, workload, diskindex)
            print('Result creation completed')
            print('************************'\
                  'Setup Cleanup Started************************\n')
            LogCreat().logger_info.info('************************'\
                                        'Setup Cleanup Started************************')
            self.un_server_vd()
            time.sleep(25)
            self.delete_vd()
            time.sleep(180)
            self.delete_pool()
            time.sleep(180)
            if vd_name.lower() != "standard":
                self.test_disable_cap_opt_at_server()
                time.sleep(30)
            print('************************'\
                  'VdBench Execution Completed************************\n')
            LogCreat().logger_info.info('************************'\
                                        'VdBench Execution Completed************************')
    def verification(self,res_json, msg):
        '''
        This method used to log INFO and ERROR to log file.
        Arguments (dict, str): res_json, msg
        Return (str): self.test_status
        '''
        try:
            if 'ErrorCode' not in res_json.keys():
                self.test_status = "Pass"
                LogCreat().logger_info.info(msg)
                print(msg)
            else:
                self.test_status = "Fail"
                print(res_json['Message'])
                LogCreat().logger_error.error(res_json['Message'])
        except:
            LogCreat().logger_error.error(res_json['Message'])
        return self.test_status
    def test_enable_cap_opt_at_server(self):
        '''
        This method Enable capacity optimization at server level.
        Arguments : None
        Return: None
        '''
        uri = "servers/" + self.server_id
        payload_dict = {
            "Operation": "EnableCapacityOptimization",
            "Disks": self.co_disk,
        }
        res = ILDC().do_enable_capacity_optimization(uri, header=None, payload=payload_dict)
        msg = "Capacity Optimization is enabled successfully at server level"
        self.verification(res.json(), msg)
    def create_diskpool(self, vd_name):
        '''
        This method create diskpool.
        Arguments : None
        Return: None
        '''
        uri = "pools"
        payload_dict = {
            "Name": "diskpool 1",
            "Server": self.server_id,
            "Disks": self.disk_pool_disk[0:1]
        }
        if vd_name.lower() != "standard":
            payload_dict["Deduplication"] = "True"
        res = ILDC().do_create_pool(uri, header=None, payload=payload_dict)
        msg = "Diskpool created successfully with CO"
        time.sleep(2)
        self.verification(res.json(), msg)
        self.pool_id = res.json()['Id']
        if len(self.disk_pool_disk) > 1 :
            self.add_disk_to_pool()
        while True:
            flag = self.reclamination()
            if flag == 1:
               break
    def add_disk_to_pool(self):
        '''
        This method add disks to diskpool.
        Arguments : None
        Return: None
        '''
        uri = "pools/" + self.pool_id
        payload_dict = {
            "Operation": "AddDisks",
            "Disks": self.disk_pool_disk[1:]
        }
        res = ILDC().do_create_pool(uri, header=None, payload=payload_dict)
        msg = "Disks are added to Diskpool"
        if str(res) == '<Response [200]>':
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def reclamination(self):
        '''
        This method verify reclamination of diskpool.
        Arguments : None
        Return (int): self.flag
        '''
        uri = "performancebytype/DiskPoolPerformance"
        res = ILDC().do_ssy_details(uri, header=None)
        if res.json() != []:
            for _ in res.json():
                for key,val in _.items():
                    if key == 'PerformanceData' and val["BytesInReclamation"] == 0:
                        self.flag = 1
            time.sleep(60)
        return self.flag
    def get_server(self):
        '''
        This method used to get server details.
        Arguments : None
        Return: None
        '''
        uri = "servers"
        res = ILDC().do_ssy_details(uri, header=None)
        self.server_id = res.json()[0]['Id']
        msg = 'Get server details'
        if str(res) == '<Response [200]>':
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def get_host(self):
        '''
        This method used to get host details.
        Arguments : None
        Return: None
        '''
        uri = 'hosts'
        res = ILDC().do_ssy_details(uri, header=None)
        msg = 'Get host details'
        if str(res) == '<Response [200]>':
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def test_disable_cap_opt_at_server(self):
        '''
        This method used to disable capacity optimization at
        server level.
        Arguments : None
        Return: None
        '''
        uri = "servers/" + self.server_id
        payload_dict = {
            "Operation": "RemoveCapacityOptimizationDisks",
            "Disks": self.co_disk,
        }
        res = ILDC().do_disable_capacity_optimization(uri, header=None, payload=payload_dict)
        msg = "Capacity Optimization is disabled successfully at server level"
        self.verification(res.json(), msg)
    def delete_pool(self):
        '''
        This method used to delete diskpool.
        Arguments : None
        Return: None
        '''
        uri = "pools/" + self.pool_id
        res = ILDC().do_pool_delete(uri)
        msg = "Diskpool deleted successfully"
        if str(res) == '<Response [200]>':
            print(msg)
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def test_create_virtual_disk(self, virtual_disk):
        '''
        This method used to create Virtual disk.
        Arguments (str): virtual disk
        Return: None
        '''
        uri = "virtualdisks"
        vd_payload = {
            "Name": virtual_disk+"_VD",
            "Description": "Description of virtual disk",
            "Size": "500GB",
            "SectorSize": "512B",
            "PoolVolumeType": "0",  # 0-stripped, 1-spanned,
            "Pool":self.pool_id,
            "Type": "0",
            "Count": "1",
        }
        res = ILDC().do_create_vd(uri, header=None, payload=vd_payload)
        msg = "Virtual disk created successfully"
        if str(res) == '<Response [200]>':
            print(msg)
            LogCreat().logger_info.info(msg)
        else:
            self.verification(json.loads(res.content), msg)
        res = json.loads(res.content)
        if len(res) != 0:
            vd_id = [x["Id"] for x in res]
            self.vd_id = vd_id[0]
    def set_vd_properties(self, virtual_disk):
        '''
        This method used to set virtual disk property.
        Arguments (str): virtual disk
        Return: None
        '''
        payload = {}
        #Once the VD is created set virtual disk properties
        if virtual_disk.lower() != "standard":
            if virtual_disk.lower().strip() == "ildc":

                payload["Deduplication"] = True
                payload["Compression"] = True
            elif virtual_disk.lower() == "ild":
                payload["Deduplication"] = True
            elif virtual_disk.lower() == "ilc":
                payload["Compression"] = True
            uri = "virtualdisks/" + self.vd_id
            res = ILDC().do_enable_cap_opt_on_vd(uri, header=None, payload=payload)
            msg = virtual_disk + " property enable at virtual disk level"
            if str(res) == '<Response [200]>':
                print(msg)
                LogCreat().logger_info.info(msg)
            else:
                self.verification(res.json(), msg)
        '''
        else:
            payload["EncryptionEnabled"] = True
            uri = "virtualdisks/" + self.vd_id
            res = ILDC().do_enable_cap_opt_on_vd(uri, header=None, payload=payload)
            msg = virtual_disk + " property enable at virtual disk level"
            if str(res) == '<Response [200]>':
                print(msg)
                LogCreat().logger_info.info(msg)
            else:
                self.verification(res.json(), msg)
        '''
    def test_serve_vd_to_host(self):
        '''
        This method used serve virtual disk to host.
        Arguments : None
        Return: None
        '''
        uri = "virtualdisks/" + self.vd_id
        serve_payload = {
            "Operation": "Serve",
            "Host": self.server_id,
            "Redundancy": "false"
        }
        res = ILDC().do_serve_vd(uri, header=None, payload=serve_payload) 
        msg = "Virtual disk server to the host"
        if str(res) == '<Response [200]>':
            print(msg)
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res, msg)
    def un_server_vd(self):
        '''
        This method used to unserve virtual disk from host.
        Arguments : None
        Return: None
        '''
        uri = "virtualdisks/" + self.vd_id
        payload_dict = {
            "Operation": "Unserve",
            "Host": self.server_id
        }
        res = ILDC().do_serve_vd(uri, header=None, payload=payload_dict)
        msg = "Unserve Virtual disk sucessfuly"
        if str(res) == '<Response [200]>':
            print(msg)
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def delete_vd(self):
        '''
        This method used to delete virtual disk.
        Arguments : None
        Return: None
        '''
        uri = "virtualdisks/" + self.vd_id
        res = ILDC().do_vd_delete(uri)
        msg = "Virtual disk deleted"
        if str(res) == '<Response [200]>':
            print(msg)
            LogCreat().logger_info.info(msg)
        else:
            self.verification(res.json(), msg)
    def stop_server(self):
        '''
        This method used to stop server.
        Arguments : None
        Return: None
        '''
        uri = "servers/" + self.server_id
        payload_dict = {
            "Operation" : "StopServer"
        }

        res = ILDC().do_serve_on_off(uri, header=None, payload=payload_dict)
        msg = "Stop server successfully"
        test_status = self.verification(res.json(), msg)
        return test_status
    def start_server(self):
        '''
        This method used to start server.
        Arguments : None
        Return: None
        '''
        uri = "servers/" + self.server_id
        payload_dict = {
            "Operation": "StartServer"
        }
        res = ILDC().do_serve_on_off(uri, header=None, payload=payload_dict)
        msg = "Start server successfully"
        test_status = self.verification(res.json(), msg)
        return test_status
    def initialize_vd(self):
        '''
        This method used to initialize virtual disk.
        Arguments : None
        Return: None
        '''
        uri = "physicaldisks"
        pd_data = Disks().do_get_physical_disks(uri, header=None)
        pd_data = json.loads(pd_data.content)
        for i in range (len(pd_data)):
            for key,val in pd_data[i].items():
                if key == "VirtualDiskId" and val in self.vd_id:
                    diskindex= pd_data[i]['DiskIndex']
                    ILDC().initial_disk(diskindex)
                    msg = "Initialized Virtual disk"
                    print(msg)
                    LogCreat().logger_info.info(msg)
                    break
        return diskindex
               
