import config.config as cf
import src.serial_lib as serial_lib
import src.colorLog as log
import os, re, time, datetime, sys,threading
import src.jlink_lib as jlink_lib
import pandas as pd
from styleframe import StyleFrame
import src.pandas_lib as pd_write
from zipfile import ZipFile
import shutil
df , columns , dict_tmp , flag_IMSI = pd.DataFrame(columns=[]) , [] , {} , False
opentime            = time.strftime( "%Y.%m.%d_%X", time.localtime() ).replace(":", "")
filename            = os.path.basename(__file__).replace('.py','')
TARGET_PORT         = 'COM10'# linux=='ttyUSBX'
MCU                 = 'STM32L071RZ'
WORK_FILE           = os.getcwd()
LOG_Folder          = os.path.join(WORK_FILE,'TEST RESULT')
os.chdir(LOG_Folder)
os.makedirs('%s-%s'%(opentime, filename))
os.chdir(WORK_FILE)
LOG_DIRECTORY       = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename))
SmartTxr_IOT1        = os.path.join(WORK_FILE,'FW','SmartTxr_IOT1.bin')
REPORT              = os.path.join(LOG_Folder, '%s-%s'%(opentime, filename), '%s_%s REPORT.xlsx'%(opentime, filename))
excel_writer        = StyleFrame.ExcelWriter(REPORT)
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
    global columns, dict_tmp, df, device_count
    jlink   = jlink_lib.jlink_module(MCU,dict_tmp, columns)
    def _parser(str_list):
        result = serial.Write(str_list[0],str_list[len(str_list)-1],read_parser=1)
        if result != []:
            for res in result:
                for str in str_list:
                    if str in res:
                        dict_tmp[str]="V"

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
               'Init RTC base',
               'gpio state = 00000111']
        _parser(check_list)


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
                    break
            if flag:break
        dict_tmp['WaitIPv4v6Ready_loop'] = WaitIPv4v6Ready_loop
        
        check_list = ['Model: WNB303R',
               'Software Version: V2071_100.0043',
               'Hardware Version: V01P2']
        serial.Set_timeout(time_out)
        _parser(check_list)

        result = serial.Write('AT+GSN','AT+CIMI',read_parser=1)
        if result != []:
            if 'AT+GSN' in result and 'AT+CIMI' in result:
                dict_tmp['IMEI']=result[1]

        check_list = ['<== MQTT publish Event (172,200) {Event/',
               'zzzZZ']
        _parser(check_list)




        serial.Close()
        log.Logger('[SYSTEM MSG] TEST END.',"BLUE","WHITE")
        exe_time=datetime.datetime.now()-start_time
        exe_time=(str(exe_time).split('.'))[0]
        print(f"{exe_time=}")
        dict_tmp["Execute time"]=exe_time


        columns= list(dict_tmp.keys())
        columns.insert(0, columns.pop(columns.index('Execute time')))
        columns.insert(0, columns.pop(columns.index('IMEI')))
        df = pd_write.write(df,dict_tmp,columns)

        f.close()
        device_count += 1
        new_filename = os.path.join(LOG_DIRECTORY, "{}_{}.txt".format(device_count,dict_tmp['IMEI']))
        os.rename(cf.get_value('logname'), new_filename)
        #for switch DEV
        while serial_lib.Port_is_open(port):pass
        print('[SYSTEM MSG] USB is disconnected')


    except KeyboardInterrupt:
        log.Logger("[SYSTEM MSG] KeyboardInterrupt", 'RED', 'WHITE',timestamp=0)
        serial.Close()
        f.close()
        jlink.close()
        if df.empty!=True: pd_write.save_to_excel(df,excel_writer,columns)
        
        # # create a ZipFile object
        # with ZipFile('%s.zip'%LOG_DIRECTORY, 'w') as zip_fp:
        #     # real all items in directory
        #     for folder_name, subfolders, filenames in os.walk(LOG_DIRECTORY):
        #         for filename in filenames:
        #             # create file's path in directory
        #             filePath = os.path.join(folder_name, filename)
        #             # Add file to zip
        #             zip_fp.write(filePath, os.path.basename(filePath))
        # shutil.rmtree(LOG_DIRECTORY)
        sys.exit("[SYSTEM MSG] Exit script")
            
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
