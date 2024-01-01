#!/usr/bin/env python3
import os
import subprocess
import platform
import json
import hashlib
import logging
from datetime import datetime

log_file = "log.log"
logging.basicConfig(filename=log_file,
                    encoding='utf-8',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def log2file(level, msg):
    logging.log(level, msg)


def log2screen(level, msg):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{current_time} - {levelToName[level]} - {msg}')


def log2both(level, msg):
    log2file(level, msg)
    log2screen(level, msg)


levelToName = {
    logging.CRITICAL: 'CRITICAL',
    logging.ERROR: 'ERROR',
    logging.WARNING: 'WARNING',
    logging.INFO: 'INFO',
    logging.DEBUG: 'DEBUG',
    logging.NOTSET: 'NOTSET',
}


def sha1_hash_string(input_string):
    # 创建一个sha1 hash对象
    sha1 = hashlib.sha1()

    # 使用输入的字符串更新hash对象
    sha1.update(input_string.encode('utf-8'))

    # 获取哈希值（十六进制字符串形式）
    hash_value = sha1.hexdigest()

    return hash_value


def get_mac_address():
    # 获取本机的网卡列表
    mac_address_list = os.popen('ipconfig /all').read().split('\n\n')

    # 遍历网卡列表，找到对应IP地址的网卡并返回MAC地址
    for mac_address in mac_address_list:
        if '物理地址' in mac_address:
            mac = mac_address.split('物理地址')[1].strip()
            mac = mac.split('\n')[0][-17:].strip()
            mac_list.append(mac)
            mac_hash.append(sha1_hash_string(mac + salt))
        if 'Physical' in mac_address:
            mac = mac_address.split('Physical')[1].strip()
            mac = mac.split('\n')[0][-17:].strip()
            mac_address_list.append(mac)
            mac_hash.append(sha1_hash_string(mac + salt))


def read_config(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            datas = json.load(f)
            return datas
    except FileNotFoundError:
        log2both(logging.ERROR,
                 f'Config file not found:{file}')
    except json.JSONDecodeError:
        log2both(logging.ERROR,
                 f'Config file format error:{file}')
    except Exception as e:
        log2both(logging.ERROR,
                 f'unknown error:{str(e)}')
    return None


def is_compressed(file_path):
    if os.path.isdir(file_path):
        return False
    else:
        command = [exe_process, 'l', '-p12345', file_path]
        # 判断是否为压缩文件
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = ""
        while True:
            output = process.stdout.readline()
            if not output:
                break
            line += output.strip().decode(errors='ignore')
        # 解压错误，说明是压缩文件
        if 'Cannot open encrypted archive. Wrong password?' in line:
            return True
        # 类型已识别出来，是压缩文件
        elif 'Type = ' in line:
            return True
        # 非压缩文件
        # 对于分卷压缩文件，但卷不完整，Cannot open the file as [7z] archive
        # 对非压缩文件，显示Cannot open the file as archive
        # 上面这两种情况，都认为非压缩文件
        elif 'Cannot open the file as' in line:
            return False
    return True


def extract_files(folder, password_list, count):
    failed_files = []

    for file_name in os.listdir(folder):
        try:
            file_path = os.path.join(folder, file_name)
            # 为了解决编码问题
            path = file_path.encode(encoding="utf-8", errors="ignore").decode()
            # 文件夹，递归处理
            if os.path.isdir(file_path):
                log2both(logging.INFO, f'(loop:{count}), dir({path})')

                # windows打包程序和7z程序放在这里面，无需解压
                if file_name == "_internal":
                    continue
                extract_files(file_path, password_list, count)

            # 压缩文件
            elif is_compressed(file_path):
                log2both(logging.INFO, f'(loop:{count}), compressed_file_path({path})')
                # 由于部分exe文件也是压缩包，此类文件不需要解压, 本程序也有可能是压缩包，跳过
                if ((ignore_format_exe and file_name.endswith(".exe")) or own_file_name1 == file_name
                        or own_file_name2 == file_name or log_file == file_name):
                    log2both(logging.INFO, f'(loop:{count}), ignore compressed_file_path({path})')
                    continue
                # 以文件名前缀，创建文件夹
                new_folder_name_list = file_name.split(".", 1)
                new_folder_path = os.path.join(folder, new_folder_name_list[0])
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                # 文件重命名,避免压缩文件与源文件同名时，出现系统占用
                new_file_path = file_path + '1'
                os.rename(file_path, new_file_path)
                # 遍历预制密码尝试解压
                for password in password_list:
                    try:
                        # 开始解压
                        subprocess.check_output(
                            [exe_process, 'x', '-p' + password, '-o' + new_folder_path, '-y', new_file_path])
                        # 解压成功，移除源文件
                        os.remove(new_file_path)
                        break
                    except subprocess.CalledProcessError as e:
                        continue
                else:
                    # 有可能是分卷压缩，此时应该恢复原来的文件名尝试解压
                    os.rename(new_file_path, file_path)
                    for password in password_list:
                        try:
                            # 开始解压
                            subprocess.check_output(
                                [exe_process, 'x', '-p' + password, '-o' + new_folder_path, '-y', file_path])
                            os.remove(file_path)
                            break
                        except subprocess.CalledProcessError as e:
                            continue
                    else:
                        # 解压失败，删除为此压缩文件创建的文件夹
                        os.removedirs(new_folder_path)
                        failed_files.append((file_name, 'Incorrect password'))
            # 非压缩文件，不处理
            else:
                continue
        except Exception as e:
            log2both(logging.ERROR, f'Capture error:{e}')
    # 记录解压失败原因
    if failed_files:
        with open(os.path.join(folder, 'failed_files.txt'), 'w', encoding='utf-8') as f:
            for file_name, reason in failed_files:
                f.write(f'{file_name}: {reason}\n')


mac_list = []
mac_hash = []
salt = "+-*/"
exe_process = "7z"
config_file = "config.json"
exec_count = 1
ignore_format_exe = True
dest_dir = '.'
password_list = []
access_code = ""
config_key_exec_count = "exec_count"
config_key_dest_dir = "dest_dir"
config_key_ignore_format_exe = "ignore_format_exe"
config_key_access_code = "access_code"
config_key_password_list = "password_list"
own_file_name1 = os.path.basename(__file__)
own_file_name2 = own_file_name1.split(".")[0]

if platform.system() == 'Windows':
    exe_process = './_internal/7z/7z.exe'
elif platform.system() == 'Linux':
    exe_process = './_internal/7z/7zz'

# 读取配置文件
data = read_config(config_file)
if data is not None:
    if config_key_exec_count in data:
        exec_count = data[config_key_exec_count]
    if config_key_dest_dir in data:
        dest_dir = data[config_key_dest_dir]
    if config_key_ignore_format_exe in data:
        ignore_format_exe = data[config_key_ignore_format_exe]
    if config_key_access_code in data:
        access_code = data[config_key_access_code]
    if config_key_password_list in data:
        password_list = data[config_key_password_list]
else:
    log2both(logging.INFO, 'use default config')

log2both(logging.INFO, "Start to unzip.")

get_mac_address()

# 校验准入码
if access_code == "":
    log2both(logging.ERROR,
             "No access code, please fill in the access code in the configuration file. If you do not have an access "
             "code, please purchase it.")
elif access_code not in mac_hash:
    log2both(logging.ERROR, "Access code error, please purchase access code.")
else:
    # 可能涉及多重解压，默认执行1次
    for i in range(exec_count):
        extract_files(dest_dir, password_list, i)
log2both(logging.INFO, "End to unzip.")
os.system('pause')
