import serial
import serial.tools.list_ports
import os, time, sys
from . import colorLog as log
import threading, queue




class Serial_Module:
    def __init__(self, port, baudrate, timeout=3, logname='', read_timeout=0.1):
        self.baudrate = baudrate
        self.port = port
        self.timeout = timeout
        self.cmd, self.expected, self.result = '', '' , ''
        self.logname = logname
        self.read_timeout = read_timeout
        self.read_parser=''

    
    def parser(self):
        try:
            multi_ps_is_alive = self.multi_ps.is_alive()
        except:
            multi_ps_is_alive = False

        if multi_ps_is_alive:
            #log.Logger('multi uart_ps is alive.')
            return True
        else:
            if Port_is_alive(self.port):
                UART = self.Connect()
            else:
                log.Logger('No ' + self.port, fore='RED' , logname=self.logname)
                return False
            if UART:
                self.multi_ps= threading.Thread(target = self.Read)
                self.multi_ps.daemon = True
                self.multi_ps.start()
                time.sleep(self.read_timeout+0.1)
                return True
            else:
                return False

    
    def get_port(self):
        return self.port


    def Read(self):
        self.stop = 0
        parser_flag=0
        while self.stop == 0 :
            if self.cmd != '':
                if self.read_parser==1:log.Logger('[SYSTEM MSG] searching parser msg "%s".'%f'{self.parser_msg}' , 'BLUE', 'WHITE', logname=self.logname)
                if self.read_parser!=1: 
                    if self.cmd != '':
                        log.Logger(' %s' %( self.cmd), 'BLACK', 'WHITE', logname=self.logname)
                # print(f'{self.read_parser=}')
                if self.read_parser==0:self.DutSer.write(str.encode(self.cmd + '\r'))
                self.cmd = ''
            try:
                tmp = self.DutSer.readline()
                try:
                    tmp = tmp.decode('ascii').replace('\n', '').replace('\r', '')

                except Exception as e:
                    log.Logger("%s, \n%s\n\n Ignore the can't decode byte." %(str(e), tmp), fore = 'RED', timestamp=0)
                    log.Logger('%s : %s' %(self.port, tmp.decode('ascii', 'ignore').replace('\n', '').replace('\r', '')), 'RED')
                    tmp = '' 
            except Exception as e:
                self.DutSer.close()
                log.Logger(str(e), fore='RED')
                log.Logger('\t\tDisconnected with Port %s...' %self.port, 'RED', timestamp=0)
                Boot_time_start = time.time()
                log.Logger('\t\tWait Booting...', timestamp=0)
                time.sleep(1)
                for i in range(600):
                    time.sleep(0.1)
                    if Port_is_alive(self.port):
                        log.Logger('\t\tBoot finished %s sec' %round(time.time() - Boot_time_start,1), timestamp=0)
                        #time.sleep(2)
                        self.Connect()
                        #log.Logger('%s : %s' %(self.port, "ATC+TSMODE=1"), 'BLACK', 'WHITE', logname=self.logname)
                        #self.DutSer.write(str.encode('ATC+TSMODE=1\r'))
                        break
                    elif i == 599:
                        log.Logger('Failed to open ' + self.port, fore='RED' , logname=self.logname)
                        return False
                    
            if self.read_parser==1 and  self.parser_msg in tmp:
                parser_flag=1


            if self.expected != '' and self.cmd == '':
                if parser_flag==1: 
                    if tmp!='':self.parserMsg.append(tmp)

                if tmp!='':self.dumpMeg.append(tmp)

                if any(string in tmp for string in self.expected) and ('?' not in tmp): 
                    parser_flag=0
                    log.Logger(' %s' %(tmp), 'GREEN', logname=self.logname)
                    if self.read_parser==1:log.Logger('[SYSTEM MSG] Find parser_msg "%s".'%self.parser_msg , 'BLUE', 'WHITE', logname=self.logname)
                    self.result = tmp
                    tmp = self.DutSer.readline().decode('ascii', 'ignore').replace('\n', '').replace('\r', '')
                elif (time.time() - self.time_start) > self.timeout:
                    self.result = False
            if tmp != '':
                log.Logger(' %s' %( tmp), logname=self.logname)
        self.DutSer.close()

    


    def Write(self, cmd, expected='', makeTrue=0, dumpAll=0,read_parser=0):
        if not expected == '':
            if type(expected) == type('string'):
                expected = [expected]
            if 'NONE' in [s.upper() for s in expected if isinstance(s, str)==True]:
                expected = ''

        retry = 0
        while True:
            try:
                multi_ps_is_alive = self.multi_ps.is_alive()
            except:
                multi_ps_is_alive = False
            if not multi_ps_is_alive:
                if not self.parser():
                    return False
            self.dumpMeg = []
            self.cmd = cmd
            self.expected = expected
            self.result = ''
            self.read_parser=read_parser
            self.parserMsg = []
            self.parser_msg=cmd
            if self.expected != '':
                self.time_start = time.time()
                while self.result == '':
                    time.sleep(self.read_timeout)
                if self.result == False and dumpAll == 0 :
                    log.Logger('[SYSTEM MSG] %s is not found.' %self.expected, fore='RED', back='WHITE', timestamp=1 , logname=self.logname)
                self.expected = ''
                if self.result or makeTrue==0 or retry >= makeTrue:

                    if read_parser==1:
                        read_parser=0
                        if len(self.parserMsg)==0:
                            # if self.dumpMeg==0:self.dumpMeg==[]
                            return self.dumpMeg
                        if len(self.parserMsg)==1:self.parserMsg=self.parserMsg[0]
                        return self.parserMsg
                    if dumpAll == 1:
                        dumpAll = 0
                        return self.dumpMeg
                    else:
                        return self.result
                if makeTrue > 1:
                    retry += 1
            else:
                # time.sleep(0.5)
                return True


    def send(self, cmd, expected='', makeTrue=0, dump_duration=0, non_block=0):
        self.orig_timeout = self.timeout
        if dump_duration > 0:
            dumpAll = 1
            self.timeout = dump_duration
        else:
            dumpAll = 0
        self.que = queue.Queue()
        self.task = threading.Thread(target=lambda q, arg1, arg2, arg3, arg4: \
                                self.que.put(self.Write(arg1, arg2, arg3, arg4)), \
                                args=( self.que, cmd, expected, makeTrue, dumpAll))
        self.task.daemon = True
        self.task.start()
        if non_block == 0 :
            self.task.join()
            self.timeout = self.orig_timeout
            return self.que.get(timeout = self.timeout)

    def send_result(self):
        try:
            self.task.join()
            self.timeout = self.orig_timeout
            return self.que.get(timeout = self.timeout)
        except:
            log.Logger('\tMulti_send is not started.', fore='GREEN', timestamp=0)
            return False

    def Connect(self):
        try:
            self.DutSer = serial.Serial(self.port, int(self.baudrate), timeout=self.read_timeout)
            return True
        except Exception as e:
            log.Logger(str(e), fore='RED')
            log.Logger('Failed to open ' + self.port, fore='RED' , logname=self.logname)
            return False
    



    def Close(self):
        self.stop = 1
        try:
            self.multi_ps.join()
        except:
            None

    
    def Set_timeout(self, timeout=''):
        if timeout=='' :
            return self.timeout
        else:
            self.timeout = int(timeout)
            
    def Set_Read_timeout(self, timeout):
        self.read_timeout = timeout
        log.Logger('\tSwitch the "flush time" to %s sec' %(timeout), 'GREEN', timestamp=0)
        self.Close()
        self.parser()



def findPort(port):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # print(f'{p.device=}')
        if p.device.find(port) != -1:return True, p.device
    return False, None


def Port_is_alive(port):
    if serial.tools.list_ports.comports() != []:
        port_list = []
        for _port in list(serial.tools.list_ports.comports()):
            port_list.append(_port[0])
        #port_list.sort()
        # print(port_list)
        if port in port_list:
            time.sleep(0.1)
            return True
    return False

def Port_is_open(port):
    if serial.tools.list_ports.comports() != []:
        port_list = []
        for _port in list(serial.tools.list_ports.comports()):
            port_list.append(_port[0])
        #port_list.sort()
        # print(port_list)
        if port in port_list:
            print("[SYSTEM MSG] Waiting for switching device...",end="\r")
            time.sleep(0.1)
            return True
    return False