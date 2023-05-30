import src.colorLog as log
import src.mqtt_lib as mqtt_lib
import src.commonFunction as commonFunction
from py_scripts import String_Handling
import src.serial_lib as serial_lib
import allure
import time, os, re
import pandas as pd


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_colwidth', 100)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

fun = commonFunction.Common()


@allure.step("Subscribe and Collect data over MQTT")
def MQTT_Subscribe(remote_ip, app_index, DevEUI, intv):
    matt = mqtt_lib.MQTT_Module(remote_ip, app_index, DevEUI)
    mesg = matt.subscribe(0, int(intv))
    return mesg


@allure.step("Parsing data and Verify Interval.")
def MQTT_Parser(data, fPort, snsr_id_type, expected_intv=60):
    log.Logger('*** Verify the interval of type %s on Probe %s should be %s' %(snsr_id_type, fPort, expected_intv), 'BLACK', 'WHITE', 0)
    handle = []
    result = 0
    if data == False:
        return result
    for i in data:
        if snsr_id_type in i['data'] and int(fPort) == i['fPort']:
            log.Logger(str(i), timestamp=0)
            handle.append(int(i['timestamp']))
            if len(handle) >= 2:
                break
    log.Logger('\tCalculation Time Interval : %s' %str(handle), fore='GREEN', timestamp=0)
    if len(handle) > 1 :
        interval = (handle[-1] - handle[-2]) 
        if abs(int(expected_intv) - interval) <= (int(expected_intv)/7):
            result += 1
    else:
        interval = 'None'
    log.Logger('\tInterval : %s' %str(interval), timestamp=0)
    return result

@allure.step("Grep all the sensor type.")
def grep_snsr_id_type(configuration_dict, snsr_index=''):
    log.Logger("*** Grep sensor's type", 'BLACK', 'WHITE', 0)
    #log.Logger('\n%s' %str(configuration_dict))
    snsr_id_type_list = []
    for i in range(1, len(configuration_dict.keys())):
        sensor_key = list(configuration_dict.keys())[i]
        sensor_info = configuration_dict[sensor_key]['INFO']
        snsr_id = sensor_key.split(':')[-1]
        snsr_id_type_list.append(snsr_id.zfill(2)+sensor_info)
    log.Logger(str(snsr_id_type_list))
    if snsr_index != '': 
        return snsr_id_type_list[snsr_index]
    else:
        return snsr_id_type_list


@allure.step("Join_LoRA_Network")
def Join_LoRA_Network(serial, NJM, cls, appkey, DevEUI, BAND, MASK='0000', ADR=1, DR=0, CFM=1):
    log.Logger("*** Join_LoRA_Network", 'BLACK', 'WHITE', 1)
    serial.parseUR()
    serial.Write('ATR', 'OK', makeTrue=1)
    time.sleep(2)
    serial.Write('ATZ', '')
    time.sleep(3)
    serial.Write('AT+NJM=%s' %NJM, '')
    serial.Write('AT+CLASS=%s' %cls.upper(), 'OK', makeTrue=1)
    serial.Write('AT+APPKEY=%s' %appkey, 'OK', makeTrue=1)
    serial.Write('AT+DEVEUI=%s' %DevEUI, 'OK', makeTrue=1)
    serial.Write('AT+BAND=%s' %BAND, 'OK', makeTrue=1)
    mask_only =  [1, 5, 6]
    if int(BAND) in mask_only:
        serial.Write('AT+MASK=%s' %MASK, 'OK', makeTrue=1)
    serial.Write('AT+ADR=0', 'OK', makeTrue=1)
    serial.Write('AT+DR=0', 'OK', makeTrue=1)
    serial.Write('AT+CFM=1', 'OK', makeTrue=1)
    serial.Set_timeout(15)
    serial.Write('AT+JOIN=1:1:8:10', '+EVT:JOINED')
    result = False
    for i in range(4):
        dump = serial.Write('AT+NJS=?', 'OK', 0, 1)
        if 'AT+NJS=1' in dump:
            result = True
            break
        else:
            serial.Write('AT+JOIN=1:1:8:10', '+EVT:JOINED')
    serial.Set_timeout(3)
    serial.Write('AT+CFM=%s' %CFM, 'OK', makeTrue=1)
    serial.Write('AT+ADR=%s' %ADR, 'OK', makeTrue=1)
    if ADR == 0 :
        serial.Write('AT+DR=%s' %DR, 'OK', makeTrue=1)
    time.sleep(2)
    serial.Close()
    return result


def grep_board_name(serial):
    #board_name = String_Handling.grep_return('AT+HWMODEL=?', serial).upper()
    dump = String_Handling.grep_return('AT+VER=?', serial)
    board_name_list = ['RAK4631', 'RAK3172','RAK3272-SiP', 'RAK3272LP-SiP', 'RAK11720']
    for board_name in board_name_list:
        if board_name in dump:
            return board_name



def grep_FQBN(serial):
    FQBN = fun.shell('arduino-cli board search %s'%grep_board_name(serial)).split(' ')[-3]
    serial.Close()
    return FQBN




def DFU_over_serial(port, FQBN, img_path):
    if os.path.isdir(img_path):
        img_path = '--input-dir %s'%img_path
    else:
        img_path = '--input-file %s'%img_path
    result = fun.shell('arduino-cli upload -v -p %s --fqbn %s %s'%(port, FQBN, img_path), ['Upgrade Complete', 'Bootload completed successfully', 'Device programmed'])
    time.sleep(5)
    for i in range(400):
        time.sleep(0.1)
        if serial_lib.Port_is_alive(port):
            break
        elif i == 399:
            log.Logger('Failed to open %s' %port, fore='RED')
            return False
    return result 


def Get_BLE_MAC(serial):
    serial.parseUR()
    ble_mac = serial.Write('ATC+BTMAC=?', expected='ATC+BTMAC=', makeTrue=1)
    if ble_mac:
        pattern = re.compile('.{2}')
        ble_mac = ble_mac.replace('ATC+BTMAC=','')
        ble_mac = ':'.join(pattern.findall(ble_mac))
    serial.Close()
    return ble_mac



@allure.step("Set interval and rule")
def Set_Configuration(serial, prb_id, prb_intv=60, snsr_index='all', snsr_intv=40, snsr_rule=8, snsr_hthr=300, snsr_lthr=100):
    log.Logger("*** Set Probe_%s intv_%s, Sensor_%s intv_%s, snsr_rule_%s, snsr_hthr_%s, snsr_lthr_%s" %(prb_id, prb_intv, snsr_index, snsr_intv, snsr_rule, snsr_hthr, snsr_lthr), 'BLACK', 'WHITE', 1)
    serial.parseUR()
    snsrid_list = []
    serial.Set_timeout(1)
    serial.Write('ATC+PRB_INFO=%s?' %prb_id, 'PRB_INFO', makeTrue=1)
    serial.Write('ATC+PRB_INTV=%s:%s' %(prb_id, prb_intv), 'OK', makeTrue=1)
    data = serial.Write('ATC+SNSR_CNT=%s?' %prb_id, 'ATC+SNSR_CNT=', makeTrue=1)
    tmp_snsr_list = []
    for i in data.split(':'):
        tmp = filter(str.isdigit, i)
        tmp = ''.join(list(tmp))
        tmp_snsr_list.append(tmp)
    tmp_snsr_list.pop(0)
    tmp_snsr_list.pop(0)

    if snsr_index == 'all': 
        for i in range(len(tmp_snsr_list)):
            snsrid_list.append('%s:%s'  %(prb_id, tmp_snsr_list[i]))
    elif len(tmp_snsr_list) < int(snsr_index)+1:
        log.Logger('snsr_index is out of range.')
        return False
    else:
        snsrid_list.append('%s:%s'  %(prb_id, tmp_snsr_list[int(snsr_index)]))
    log.Logger('Sensor List : %s' %snsrid_list, fore='GREEN')
    cmd_list = ['INTV=$snsr_id:%s' %snsr_intv, 'RULE=$snsr_id:%s' %snsr_rule, 'HTHR=$snsr_id:%s' %snsr_hthr, 'LTHR=$snsr_id:%s' %snsr_lthr]
    for i in snsrid_list:  
        for cmd in cmd_list:
            serial.Write('ATC+SNSR_%s' %(cmd.replace('$snsr_id', i)), 'OK', makeTrue=1)
        serial.Set_timeout(3)
    serial.Write('', '+EVT:UPD_SENSR: %s'%i)
    serial.Close()



@allure.step("Get interval and rule")
def Get_Configuration(serial, prb_id):
    log.Logger("*** Get interval and rule on Probe_%s" %prb_id, 'BLACK', 'WHITE', 1)
    serial.parseUR()
    configuration_dict = {} 
    snsrid_list = []
    serial.Set_timeout(3)
    serial.Write('ATC+PRB_INFO=%s?' %prb_id, '')
    data = serial.Write('ATC+PRB_INTV=%s?' %prb_id, 'ATC+PRB_INTV', makeTrue=1)
    configuration_dict['%s_INTV' %prb_id] = re.findall('PRB_INTV=%s:([^?].*)'%prb_id, data)[0]
    data = serial.Write('ATC+SNSR_CNT=%s?' %prb_id, 'ATC+SNSR_CNT=', makeTrue=1)
    tmp_snsr_list = []
    for i in data.split(':'):
        tmp = filter(str.isdigit, i)
        tmp = ''.join(list(tmp))
        tmp_snsr_list.append(tmp)
    tmp_snsr_list.pop(0)
    tmp_snsr_list.pop(0)

    for i in range(len(tmp_snsr_list)):
        snsrid_list.append('%s:%s'  %(prb_id, tmp_snsr_list[i]))
    log.Logger('Sensor List : %s' %snsrid_list, fore='GREEN')

    for i in snsrid_list:
        inner_key = ['ATC+SNSR_INFO=%s' %i, 'ATC+SNSR_INTV=%s' %i, 'ATC+SNSR_RULE=%s' %i, 'ATC+SNSR_HTHR=%s' %i, 'ATC+SNSR_LTHR=%s' %i]
        inner_value = []
        for cmd in inner_key:
            data = serial.Write(cmd+'?', cmd, makeTrue=1)
            inner_value.append(data.replace(cmd+':', ''))
        inner_key = ['INFO', 'INTV', 'RULE', 'HTHR', 'LTHR']
        inner_dict = dict(zip(inner_key, inner_value))
        configuration_dict[i] = inner_dict
    serial.Close()
    configuration_df  = configuration_dict.items()
    configuration_df = pd.DataFrame(list(configuration_df),columns=['key', 'value']).set_index("key")
    log.Logger('\n'+str(configuration_df), timestamp=0)
    return configuration_dict



