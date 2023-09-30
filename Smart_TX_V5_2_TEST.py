import config.config as cf
import sys
import src.serial_lib as serial_lib
import src.colorLog as log
import os, re, time, datetime, sys,threading
import src.jlink_lib as jlink_lib
import pandas as pd
import src.pandas_lib as pd_write
from zipfile import ZipFile
import shutil
import re 




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
MCU                 = 'STM32L071RZ'
WORK_FILE           = os.getcwd()
LOG_Folder          = os.path.join(WORK_FILE,'TEST RESULT')
os.chdir(LOG_Folder)
os.makedirs('%s-%s'%(opentime, filename))
os.chdir(WORK_FILE)
LOG_DIRECTORY       = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename))
#SmartTxr_IOT1        = os.path.join(WORK_FILE,'FW','SmartTxr_IOT1_v5.2.1.1.0.bin')
SmartTxr_IOT1       ='SmartTxr_IOT1_v5.2.1.1.0.bin'
REPORT              = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename), '%s_%s REPORT.xlsx'%(opentime, filename))
pandas = pd_write.pandas_Module(excel_name=REPORT)
CHECK_PARSERMSG_LIST= [ # 'SmartTxr_IOT1_',
                        # 'Init RTC base',
                        # 'gpio state = 00000111',
                        # 'Model: WNB303R',
                        # 'Software Version: V2071_100.0043',
                        # 'Hardware Version: V01P2',
                        # 'zzzZZ',
                        # 'Current gpio state = 00000110',
                        # 'GPIO_PORT_1...0',
                        # 'zzzZZ',
                        # 'Current gpio state = 00000101',
                        # 'GPIO_PORT_2...0',
                        # 'zzzZZ',
                        # 'Current gpio state = 00000011',
                        # 'GPIO_PORT_3...0',
                        # '<== MQTT publish Event (172,200) {Event/',
                        # 'zzzZZ'
                       ]#The annotated strings are cannot be found.




                        
def main():
    global columns, dict_tmp, device_count

    def _parser(str_list):
        result = serial.Write(str_list[0],str_list[len(str_list)-1],read_parser=1)
        if result != []:
            for res in result:
                for str in str_list:
                    if str in res:
                        dict_tmp[str]="V"


    def _parser_value(str_list):
        result = serial.Write(str_list[0],str_list[len(str_list)-1],read_parser=1)
        if result != []:
            for res in result:
                for str in str_list:
                    if str in res:
                        if 'MCELLINFOSC' in str :
                            dict_tmp[str]=''
                            numbers = re.findall(r'(-?\d+)', res)
                            if(len(numbers)>4):
                                numbers = [int(num) for num in numbers]
                                dict_tmp[str]=numbers[3]                                
                        elif 'CCLK' in str:
                            dict_tmp[str]=''
                            pattern = r'\+CCLK:(\d{4}/\d{2}/\d{2}),(\d{2}:\d{2}:\d{2})GMT\+\d+'
                            match = re.search(pattern, res)
                            if match:
                                date = match.group(1)
                                time = match.group(2)
                                dict_tmp[str]=date+'  '+time
                        else:
                            pattern = str+r"(\S+)"
                            match = re.search(pattern, res)
                            if match:
                                dict_tmp[str] = match.group(1)
       
    while True: 
        sn_str = input("Enter S/N: ")
        try:
            number = int(sn_str)
            break
        except ValueError:
            print("Invalid input. Please enter again")
    
    dict_tmp['SN'] = 'LPG5P2B002309-'+ f"{number:04d}"
    
    jlink   = jlink_lib.jlink_module(MCU,dict_tmp, columns)

    time_out=60
    serial.Set_timeout(time_out)
    try:
        start_time=datetime.datetime.now()
        jlink.reboot()
        
        while True:
            flash_result= jlink.flash_file(file=SmartTxr_IOT1)
            if flash_result:break


        threading.Thread(target=jlink.reboot,args=(1.5,)).start()
        time.sleep(1)

        check_list = ['SmartTxr_IOT1_',
               'gpio state = ', 
               'Current PVD state = ']
        _parser_value(check_list)


        serial.Set_timeout(5)
        WaitIPv4v6Ready_loop = 0
        
        while True:
            flag = False
            res = serial.Write('','+IP:',dumpAll=1)
            for r in res:
                if 'WaitIPv4v6Ready' in r :
                    WaitIPv4v6Ready_loop += 1
                    continue
                if '+IP:' in r : 
                    flag = True
                    dict_tmp['IP']=''
                    pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    match = re.search(pattern, r)   
                    if match:
                        ip_address = match.group(0)
                        if ip_address != '127.0.0.1':
                            dict_tmp['IP']=ip_address 
                            print(dict_tmp['IP'])
                    break
            if flag:break
        dict_tmp['WaitIPv4v6Ready_loop'] = WaitIPv4v6Ready_loop
        

        # check NB-IOT Modem model name and Version
        check_list = ['Model: ', 
                      'Software Version: ', 
                      'Hardware Version: '
                     ]
        serial.Set_timeout(time_out)
        _parser_value(check_list)
        

        #Get IMEI
        result = serial.Write('AT+GSN','AT+CIMI',read_parser=1)
        if result != []:
            if 'AT+GSN' in result and 'AT+CIMI' in result:
                dict_tmp['IMEI']=result[1]
        
        # Get RSSI  
        check_list = ['*MCELLINFOSC:','+CCLK']
        serial.Set_timeout(time_out)
        _parser_value(check_list)  

        # Completed   
        check_list = ['AT+EMQNEW=\"iot1.wavein.com.tw\",\"18883\",60000,1536',
                      'MQTT publish Event (178,200)',
                      'zzzZZ'
                     ]
        _parser(check_list)


        serial.Close()
        log.Logger('[SYSTEM MSG] TEST END.',"BLUE","WHITE")
        exe_time=datetime.datetime.now()-start_time
        exe_time=(str(exe_time).split('.'))[0]
        print(f"{exe_time=}")
        dict_tmp["Execute time"]=exe_time

        columns= list(dict_tmp.keys())
        dict_tmp = move_to_front(dict_tmp, 'Execute time')
        dict_tmp = move_to_front(dict_tmp, 'IMEI')
        dict_tmp = move_to_front(dict_tmp, 'SN')
        pandas.write(dict_tmp)

        f.close()
        device_count += 1
        new_filename = os.path.join(LOG_DIRECTORY, "{}_{}.txt".format(device_count,dict_tmp['IMEI']))
        os.rename(cf.get_value('logname'), new_filename)


        #for switch DEV
        #while serial_lib.Port_is_open(port):
        #print('[SYSTEM MSG] USB is disconnected')


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
    if len(sys.argv)> 1:
        TARGET_PORT = sys.argv[1]
    else:
        TARGET_PORT = 'COM7'# linux=='ttyUSBX'
    print(f"Opening UART port {TARGET_PORT}")
    
    while True:
        try:
            f=open(cf.get_value('logname'),'w')
            flag_find, port = serial_lib.findPort(TARGET_PORT)
            dict_tmp.clear()
            columns.clear()
            if flag_find is True:
                log.Logger("[SYSTEM MSG] Connecting to {}".format(port),fore='GREEN',timestamp=0)
                serial  = serial_lib.Serial_Module(port, 115200, 3, '', 0.01)
                while True:
                    if serial.parser():break
                main()
            else:
                print("[SYSTEM MSG] Waiting for the USB plugged in...",end="\r")
                time.sleep(0.1)
                continue
        
        except Exception as e:
            log.Logger("[SYSTEM MSG] Searching PORT Error len : %s, %s"%(e.__traceback__.tb_lineno, e),fore='RED',timestamp=0)
            serial.Close()
            f.close()
            while serial_lib.Port_is_open(port):pass
