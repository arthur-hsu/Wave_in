import os, time
from config.lab_config import lab


def init():
    global _global_dict
    _global_dict = {}

    logFolder =  time.strftime( "%Y.%m.%d_%X", time.localtime() ).replace(":", "")
    root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    report_dir = '%s/_log/%s/' %(root_dir, logFolder)
    _global_dict['root_dir'] = root_dir+'/'

    _global_dict['report_path'] = report_dir

    _global_dict['screenshot_path'] = "{}screenshot/".format(report_dir)
    #下載資料夾
    #_global_dict['download_path'] = "{}download/".format(report_dir)
    # 上傳資料夾
    #_global_dict['upload_path'] = "{}upload/".format(report_dir)
    _global_dict['logname'] = 'collect_test'

    current_os = os.popen('uname -a')
    info = ''
    for i in current_os.readlines():
        info += '%s' %i 
    _global_dict['current_os'] = info 
    # pandas DF
    _global_dict['report_table'] = None

    _global_dict['driver'] = None

    _global_dict['lab'] = lab

    # for i in _global_dict.keys():
    #     if 'path' in i and not os.path.exists(_global_dict[i]):
    #         os.makedirs(_global_dict[i])

def set_value(name, value):
    """修改全域性變數的值
        :param name: 變數名
        :param value: 變數值
    """
    _global_dict[name] = value
    

def get_value(name, def_val='no_value'):
    """ 獲取全域性變數的值 
        :param name: 變數名 
        :param def_val: 預設變數值 
        :return: 變數存在時返回其值，否則返回'no_value'
    """ 
    try: 
        return _global_dict[name]
    except :
        return def_val
