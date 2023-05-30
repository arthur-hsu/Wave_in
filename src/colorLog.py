from colorama import init, Fore, Back, Style
import os, time, platform,datetime
import config.config as cf

fore_dict = {'None': '', 'GREEN': Fore.GREEN, 'RED': Fore.RED, 'YELLOW': Fore.YELLOW, 'BLACK': Fore.BLACK,\
             'CYAN': Fore.CYAN, 'BLUE': Fore.BLUE, 'WHITE': Fore.WHITE}
back_dict = {'None': '', 'None': '', 'WHITE': Back.WHITE, 'YELLOW': Back.YELLOW, 'BLACK':Back.BLACK}

#Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
#Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
if 'Windows' in platform.system():
    init(wrap=True)

def Logger( log, fore = 'None', back = 'None', timestamp = 1, logname=''):
    if timestamp == 1:
        log = '[%s]  %s' %(datetime.datetime.now(), log)
    if logname == '':
        logname = cf.get_value('logname')
    f = open(logname, 'a')
    print('%s' %log, file = f)
    f.close()
    if fore != 'None' or back != 'None':
        log = '%s%s%s%s' %(fore_dict[fore], back_dict[back], log, Style.RESET_ALL)    
    print('\n%s' %log)
