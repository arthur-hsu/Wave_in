import sys
import config.config as cf
import src.serial_lib as serial_lib
import src.colorLog as log
import os, re, time, datetime, sys
import src.jlink_lib as jlink_lib
import pandas as pd
from styleframe import StyleFrame
import src.pandas_lib as pd_write


def move_to_front(dictionary, key_to_move):
    # 创建一个新的字典
    new_dict = {key_to_move: dictionary[key_to_move]}
    # 遍历原始字典，跳过要移到前面的键值对
    for key, value in dictionary.items():
        if key != key_to_move:
            new_dict[key] = value
    return new_dict

columns , dict_tmp , flag_IMSI =  [] , {} , False

opentime            = time.strftime( "%Y.%m.%d_%X", time.localtime() ).replace(":", "")
filename            = os.path.basename(__file__).replace('.py','')
MCU                 = 'STM32F303RE'
WORK_FILE           = os.getcwd()
LOG_Folder          = os.path.join(WORK_FILE,'TEST RESULT')
os.chdir(LOG_Folder)
os.makedirs('%s-%s'%(opentime, filename))
os.chdir(WORK_FILE)
LOG_DIRECTORY       = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename))
PEM_HEX             = os.path.join(WORK_FILE,'FW','BLwAPP_BG96_PEM_UploadRm.hex')
ALL_23318_HEX       = os.path.join(WORK_FILE,'FW','all_23318.hex')
REPORT              = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename), '%s_%s REPORT.xlsx'%(opentime, filename))
pandas = pd_write.pandas_Module(excel_name=REPORT)
CHECK_PARSERMSG_LIST= ["WI 2022.07.12 t02",
                       "IOTBOX FW version : 23318",
                       "Power normal",
                       "e_State_Box_MeterProcess",
                    #    "LPG meter code: 22A8D6031635",
                    #    "LPG meter code: 22A000231460",
                       "Gate is released",
                       "e_State_Mod_Init",
                       "SIM card from Taiwan",
                       "Normal signal detected",
                       "e_State_Mod_NWCheck",
                       "RSRP :",
                       "e_State_Mod_MQTT_Connect",
                       "MQTT server connection: success",
                       "MQTT server ping: success",
                       "e_State_Mod_MQTT_Send",
                       "Degree transmitted",
                    #    "e_State_Mod_MQTT_FlagRequest",
                    #    "IOTBOX no need to OTA",
                    #    "Control flags received",
                    #    "MQTT subscribe success",
                    #    "e_State_Mod_HTTPS_Request",
                    #    "HTTP POST Header received",
                    #    "e_State_Box_BOXSleep",
                    #    "Enter sleep mode.",
                    #    "BG96 power off."
                        ]   #The annotated strings are cannot be found


def main():
    global columns, dict_tmp, device_count
    

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


    while True: 
        sn_str = input("Enter S/N: ")
        try:
            number = int(sn_str)
            break
        except ValueError:
            print("Invalid input. Please enter again")
    
    dict_tmp['SN'] = 'LPG5P2B002309-'+ f"{number:04d}"
    
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
        device_count += 1
        # print(f"{dict_tmp=}")
        # print(f"{columns=}")


        while True:
            jlink.reboot()
            flash_result= jlink.flash_file(file=ALL_23318_HEX)
            if flash_result:break

        loop_2=0
        for _parserMsg in CHECK_PARSERMSG_LIST:
            loop_2=keyword_parser(_parserMsg,loop_2)
            # print(f"{loop_2=}")
            # print(f"{columns=}")
            # print(f"{dict_tmp=}")

        dict_tmp['loop_2']=loop_2


        IMEI_msg='IMEI'
        time_out=20
        serial.Set_timeout(time_out)
        loop_3=0
        while True:
                result=serial.Write(IMEI_msg,IMEI_msg,read_parser=1)
                # print(f'{result=}')#test
                if result==[]:
                    loop_3+=1
                    log.Logger('[SYSTEM MSG] System no response in %ss, Reburning file.'%time_out,'RED','WHITE',timestamp=1)
                    while not jlink.flash_file(file=ALL_23318_HEX,rec=0):pass
                    print(f'{loop_3=}')
                if len(result)!=0 and IMEI_msg not in result:
                    log.Logger('[SYSTEM MSG] Result not empty, keep searching.',"BLUE","WHITE")
                    continue
                if IMEI_msg in result:
                    serial.Close()
                    log.Logger('[SYSTEM MSG] TEST END.',"BLUE","WHITE")
                    exe_time=datetime.datetime.now()-start_time
                    exe_time=(str(exe_time).split('.'))[0]
                    print(f"{exe_time=}")
                    
                    columns.insert(0, "Execute time")
                    dict_tmp["Execute time"]=exe_time

                    columns.insert(0, "IMEI")
                    IMEI = re.search("IMEI : (.*)", result).group(1)
                    print(f"{IMEI=}")
                    dict_tmp["IMEI"]=IMEI

                    dict_tmp['rety find IMEI']=loop_3
                    dict_tmp = move_to_front(dict_tmp, 'Execute time')
                    dict_tmp = move_to_front(dict_tmp, 'IMEI')
                    dict_tmp = move_to_front(dict_tmp, 'SN')

                    pandas.write(dict_tmp)


                    f.close()
                    new_filename = os.path.join(LOG_DIRECTORY, "{}_{}.txt".format(device_count,IMEI))
                    os.rename(cf.get_value('logname'), new_filename)
                    #for switch DEV
                    # while serial_lib.Port_is_open(port):pass
                    # print('[SYSTEM MSG] USB is disconnected')
                    #for switch DEV
                    break
    except KeyboardInterrupt:
        log.Logger("[SYSTEM MSG] KeyboardInterrupt", 'RED', 'WHITE',timestamp=0)
        serial.Close()
        f.close()
        jlink.close()
        return
    except Exception as e:
        print('Error len : %s, %s'%(e.__traceback__.tb_lineno, e))
        log.Logger("[SYSTEM MSG] Error len : %s, %s"%(e.__traceback__.tb_lineno, e),fore='RED',timestamp=0)
        f.close()
        jlink.close()
        print('fail')
        while serial_lib.Port_is_open(port):pass


if __name__ == '__main__':
    
    device_count = 0
    port = ''
    cf.init()
    cf.set_value('logname', '%s' % (os.path.join(LOG_DIRECTORY, "origin.txt")))#old log file
    f=open(cf.get_value('logname'),'w')
    if len(sys.argv)> 1:
        TARGET_PORT = sys.argv[1]
    else:
        TARGET_PORT = 'COM7'# linux=='ttyUSBX'
        # TARGET_PORT = input().upper()
    while True:
        try:
            dict_tmp.clear()
            columns.clear()
            flag_find, port = serial_lib.findPort(TARGET_PORT)
            if flag_find is True:
                log.Logger("[SYSTEM MSG] Connecting to {}".format(port),fore='GREEN',timestamp=0)
                start_time=datetime.datetime.now()
                serial  = serial_lib.Serial_Module(port, 115200, 3, '', 0.01)
                jlink   = jlink_lib.jlink_module(MCU, dict_tmp, columns)
                main()
            else:
                print("[SYSTEM MSG] Waiting for the USB plugged in...",end="\r")
                time.sleep(0.1)
                continue
        except Exception as e:
            log.Logger("[SYSTEM MSG] Searching PORT Exception '{}' happened\r\n".format(e),fore='RED',timestamp=0)
            serial.Close()
            jlink.close()
            f.close()
