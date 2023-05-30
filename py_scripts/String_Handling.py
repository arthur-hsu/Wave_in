import time, os, re
import src.colorLog as log
import src.serial_lib as serial_lib
import random





def Convert_txt_file_to_list(file_path, file):
    fp = open(file_path+file, "r", encoding='utf-8')
    atcmd_list=[]
    i = 0
    while True :
        tmp = fp.readline().replace('\ufeff', '').replace('\n','')
        #tmp = fp.readline().replace('\n','')
        if tmp == 'break' or i > 50:
            break
        elif tmp == '':
            i += 1
        else:
            i = 0
            tmp = tmp.split('    ')
            #if len(tmp)>1:
            tmp.append('Story:%s' %file)
            atcmd_list.append(tmp)
    return atcmd_list



def Convert_String_for_re_module(string):
    string = string.replace(' ', '\s').replace('(', '[(]').replace(')', '[)]').replace('.', '[.]').replace('+','\\+')
    return string

def Random_Hex(length):
    length = int(length)
    hex_string = hex(random.randint(0,16**length)).replace('0x','').upper()
    if(len(hex_string)<length):
        hex_string = '0'*(length-len(hex_string))+hex_string
    return hex_string

def Filter_Number(string):
    handle = string
    handle = filter(str.isdigit, handle)
    handle = ''.join(list(handle))
    return int(handle)


def string_to_list_remove_empty(string, handle):
#### .strip(' ') 去掉最左右兩邊的指定符號
    string_list = string.split(handle)
### remove empty from list
    string_list = list(filter(None, string_list))
    new_list = []
    for i in string_list:
        new_list.append(i.strip(' '))
    return new_list


def grep_return(cmd, serial):
    if type(serial) == type('string'):
        serial = serial_lib.Serial_Module(serial, 115200)
        if not serial.parseUR() :
            return 'NONE'
    cmd = cmd.upper()
    dump = serial.Write(cmd, 'OK', makeTrue=3, dumpAll=1)
    dump = re.findall("%s([^?].*)\n"%Convert_String_for_re_module(cmd.replace('?','')), dump)
    serial.Close()
    if len(dump)>0:
        return dump[0]
    else:
        return 'NONE'




def grep_version(serial):
    ver = ''
    inquiry_ver = ['VER=', 'REPOINFO=']
    for cmd in inquiry_ver:
        dump = serial.Write('AT+%s?'%cmd,cmd, makeTrue=1, dumpAll=1)
        dump = re.findall("%s([^?].*)\n"%cmd, dump)
        if len(dump)>0:
            ver += dump[0] + '\n'
    return ver



