import config.config as cf
import src.serial_lib as serial_lib
from serial.tools import list_ports
import src.colorLog as log
import sys
import os, re, time, inspect, pylink


WORK_FILE       = os.getcwd()
LOG_DIRECTORY   = os.path.join(WORK_FILE,'log')
PEM_HEX         = os.path.join(WORK_FILE,'NB_test','BLwAPP_BG96_PEM_UploadRm.hex')
ALL_23318_HEX   = os.path.join(WORK_FILE,'NB_test','all_23318.hex')
REPORT          = os.path.join(WORK_FILE,'REPORT.xlsx')

class jlink_module():
    def __init__(self,MCU ,dict_tmp,columns):
        self.jlink      = pylink.JLink()
        self.dict_tmp   = dict_tmp
        self.columns    = columns
        self.MCU        = MCU
    def flash_file(self, file, rec=1):
        # print(self.dict_tmp, self.excel, self.df)
        try:
            caller_globals = inspect.currentframe().f_back.f_globals
            for name, value in caller_globals.items():
                if value is file:
                    dict_key=f"{name}"
                    # print(dict_key)
                    break
            log.Logger('[SYSTEM MSG] Jlink flash_file=%s.'%file, 'BLUE', 'WHITE')
            self.jlink.open()
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            self.jlink.connect(self.MCU)
            self.jlink.reset()
            if file==PEM_HEX:
                log.Logger('[SYSTEM MSG] erase chip.', 'BLUE', 'WHITE')
                self.jlink.erase()
            self.jlink.flash_file(file, 0)

            log.Logger('[SYSTEM MSG] Jlink flash done.', 'BLUE', 'WHITE')
            if rec==1 :
                # self.columns.append('%s_upload'%dict_key)
                self.dict_tmp['Flash %s'%dict_key]='V'
                # print(f'{self.columns=}',f'{self.dict_tmp=}')
            self.jlink.reset()
            self.jlink.close()
            return True

        except Exception as e:
            self.jlink.clear_error()
            self.jlink.close()
            log.Logger("[SYSTEM MSG] Flash Procedure Exception {} happened".format(e),fore='RED')
            time.sleep(5)
            return False
    def reboot(self, delay_time=0):
        if delay_time!=0:time.sleep(delay_time)
        try:
            log.Logger('[SYSTEM MSG] Jlink reboot device.', 'BLUE', 'WHITE')
            self.jlink.open()
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            self.jlink.connect(self.MCU)
            self.jlink.reset()
            self.jlink.close()
            # log.Logger('[SYSTEM MSG] Jlink reboot finished.', 'BLUE', 'WHITE')
            return True
        except Exception as e:
            self.jlink.clear_error()
            self.jlink.close()
            log.Logger("[SYSTEM MSG] Reboot Procedure Exception {} happened".format(e),fore='RED')
            time.sleep(2)
            return False
    def close(self):
        self.jlink.clear_error()
        self.jlink.close()
