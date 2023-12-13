#!/usr/bin/env python3
import os
import subprocess
import platform
import json


def read_config(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            datas = json.load(f)
            return datas
    except FileNotFoundError:
        print(f'Config file not found:{file}')
    except json.JSONDecodeError:
        print(f'Config file format error:{file}')
    except Exception as e:
        print(f'unknown error:{str(e)}')
    return None


def is_compressed(file_path):
    if os.path.isdir(file_path):
        return False
    else:
        command = [exe_process, 'l', '-p12345', file_path]
        # 判断是否为压缩文件
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            output = process.stdout.readline()
            if process.poll() is not None:
                break
            if output:
                line = output.strip().decode(errors='ignore')
                # 解压错误，说明是压缩文件
                if 'Cannot open encrypted archive. Wrong password?' in line:
                    process.communicate()
                    return True
                # 非压缩文件
                elif 'Cannot open the file as archive' in line:
                    process.communicate()
                    return False
                # 类型已识别出来，是压缩文件
                elif 'Type = ' in line:
                    process.communicate()
                    return True
    return True


def extract_files(folder, password_list, count):
    failed_files = []

    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        # 为了解决编码问题
        path = file_path.encode(encoding="utf-8", errors="ignore").decode()
        # 文件夹，递归处理
        if os.path.isdir(file_path):
            print(f'(loop:{count}), dir({path})')

            # windows打包程序和7z程序放在这里面，无需解压
            if file_name == "_internal":
                continue
            extract_files(file_path, password_list, count)

        # 压缩文件
        elif is_compressed(file_path):
            print(f'(loop:{count}), file_path({path})')
            # 由于部分exe文件也是压缩包，此类文件不需要解压, 本程序也有可能是压缩包，跳过
            if file_name.endswith(".exe") or own_file_name1 == file_name or own_file_name2 == file_name:
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
                        subprocess.check_output([exe_process, 'x', '-p' + password, '-o' + folder, '-y', file_path])
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

    # 记录解压失败原因
    if failed_files:
        with open(os.path.join(folder, 'failed_files.txt'), 'w', encoding='utf-8') as f:
            for file_name, reason in failed_files:
                f.write(f'{file_name}: {reason}\n')


exe_process = "7z"
config_file = "config.json"
exec_count = 1
dest_dir = '.'
password_list = []
config_key_exec_count = "exec_count"
config_key_dest_dir = "dest_dir"
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
    if config_key_password_list in data:
        password_list = data[config_key_password_list]
else:
    print(r'use default config')

# 可能涉及多重解压，默认执行1次
for i in range(exec_count):
    extract_files(dest_dir, password_list, i)
