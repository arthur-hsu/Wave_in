import os,json, sys,time



def init(opentime='', filename=''):
    global _global_dict
    _global_dict = {}
    if opentime == '' : opentime = time.strftime( "%Y%m%d_%X", time.localtime() ).replace(":", "")
    if filename == '' : filename = os.path.basename(sys.argv[0]).replace('.py','')
    # work_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    work_dir = os.getcwd()
    print(work_dir)
    if not os.path.exists("report"):os.makedirs(os.path.join(work_dir, 'report'))
    report_dir = os.path.join(work_dir, "report",filename, f"{filename}_{opentime}")

    _global_dict['work_dir']    = work_dir
    _global_dict['report_dir']  = report_dir
    _global_dict['config_dir']  = os.path.join(work_dir,'config')
    _global_dict['fw_dir']      = os.path.join(work_dir,'Firmware')
    _global_dict['tmp_dir']     = os.path.join(work_dir,'.tmp')
    _global_dict['tmp_file']    = os.path.join(work_dir,'.tmp', f"{filename}_tmp.json")
    _global_dict['logname']     = f"{filename}_{opentime}"

    for i in _global_dict.keys():
        if 'dir' in i and not os.path.exists(_global_dict[i]):
            os.makedirs(_global_dict[i])
        if 'file' in i:
            if not os.path.exists(_global_dict[i]):
                f = os.open(_global_dict[i],os.O_RDWR|os.O_CREAT)
                os.write(f,'{}'.encode())
                os.close(f)
            try:
                with open(_global_dict[i],'r') as f : tmp_ = json.load(f)
            except json.decoder.JSONDecodeError as e:
                print(e)
                f = os.open(_global_dict[i],os.O_RDWR|os.O_CREAT)
                os.write(f,'{}'.encode())
                os.close(f)



def set_value(name, value):
    """修改全域性變數的值
        :param name: 變數名
        :param value: 變數值
    """
    if type(value) == list:
        value = os.path.join(*value)
    _global_dict[name] = value
    print(f"Set {name} : {get_value(name)}")

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
