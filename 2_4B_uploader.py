import config.config as cf
import src.serial_lib as serial_lib
import src.colorLog as log
import os, re, time, datetime, sys
import src.jlink_lib as jlink_lib
import pandas as pd
import src.pandas_lib as pd_write



MCU                 = 'STM32F303RE'
WORK_FILE           = os.getcwd()
PEM_HEX             = os.path.join(WORK_FILE,'FW','BLwAPP_BG96_PEM_UploadRm.hex')
ALL_23318_HEX       = os.path.join(WORK_FILE,'FW','all_23318.hex')

CHECK_PARSERMSG_LIST= ["WI 2022.07.12 t02",
                       "IOTBOX FW version : 23318",]


def run():
    dict_tmp = {}

    def keyword_parser(parser_msg,loop):
        begin_loop=loop
        Rety_time=1 # times of find parser Rety_time=1 mean reflash 1 times and searching 2 times.
        while True:
            result=serial.Write(parser_msg,parser_msg,read_parser=1)
            # print(f'{result=}')
            if result==[]:
                    loop+=1
                    log.Logger('[SYSTEM MSG] System no response in %ss, reflash file.'%time_out,'RED','WHITE',timestamp=1)
                    print(f"{loop=}")
                    while not jlink.flash_file(file=ALL_23318_HEX,rec=0):pass
            if result !=[] and parser_msg not in result: 
                log.Logger('[SYSTEM MSG] Result not empty, keep searching.',"BLUE","WHITE")
                continue
            if parser_msg in result:
                dict_tmp[parser_msg]="V"
                # print(f"{dict_tmp=}")
                # print('reboot times= %s'%loop)
                return loop
            if loop>=(begin_loop+Rety_time) and parser_msg not in result:
                dict_tmp[parser_msg]="X"
                # print(f"{dict_tmp=}")
                # print('reboot times= %s'%loop)
                return loop


    
    time_out=20
    serial.Set_timeout(time_out)
    if not serial.parser():
        return
    try:
        jlink.reboot()
        while True:
            flash_result= jlink.flash_file(file=PEM_HEX)
            '''
            ##DEBUG##
            print(f"{dict_tmp=}")
            print(f"{columns=}")
            '''
            if flash_result:break
        loop_1=0
        while True:
            result=serial.Write('IOTBoxCA.pem has been uploaded.',"IOTBoxKey.pem has been uploaded.",read_parser=1)
            # print(f'{result=}')
            if result ==['IOTBoxCA.pem has been uploaded.', 'IOTBoxCC.pem has been uploaded.', 'IOTBoxKey.pem has been uploaded.']: 
                dict_tmp['rety find 3.pem']=loop_1
                break
            if result !=[] and result!=['IOTBoxCA.pem has been uploaded.', 'IOTBoxCC.pem has been uploaded.', 'IOTBoxKey.pem has been uploaded.']: 
                log.Logger('[SYSTEM MSG] Result not empty, keep searching.',"BLUE","WHITE")
                if 'IOTBoxCA.pem has been uploaded.' not in result and ('IOTBoxCC.pem has been uploaded.' and 'IOTBoxKey.pem has been uploaded.') in result:
                    loop_1+=1
                    log.Logger('[SYSTEM MSG] Not find "IOTBoxCC.pem has been uploaded.", reboot.','BLUE','WHITE',timestamp=1)
                    while not jlink.reboot():pass
                continue
            if result ==[]:
                loop_1+=1
                log.Logger('[SYSTEM MSG] 3 of ".pem" file has not been uploaded, reboot.','BLUE','WHITE',timestamp=1)
                # while not jlink.flash_file(file=PEM_HEX,rec=0):pass
                # time.sleep(2)
                while not jlink.reboot():pass


        while True:
            jlink.reboot()
            flash_result= jlink.flash_file(file=ALL_23318_HEX)
            if flash_result:break

        loop_2=0
        for _parserMsg in CHECK_PARSERMSG_LIST:
            loop_2=keyword_parser(_parserMsg,loop_2)
        serial.Close()
    except KeyboardInterrupt:
        return




if len(sys.argv)> 1:
    port = sys.argv[1]
else:
    port = 'COM7'# linux=='ttyUSBX'
    # TARGET_PORT = input().upper()
serial  = serial_lib.Serial_Module(port, 115200, 3, '', 0.01)
jlink   = jlink_lib.jlink_module(MCU)
device_count=1
while True:
    input('Press Enter to continue...')
    run()
    print(f"Finish {device_count} devices.")
    device_count+=1


