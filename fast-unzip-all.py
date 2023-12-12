#!/usr/bin/env python3
import os
import subprocess
import platform

def read_passwords(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                passwords.append(line.strip())
    except FileNotFoundError:
        print(f"File not found ：{file_path}")


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
        # 文件夹，递归处理
        if os.path.isdir(file_path):
            print(f'(loop:{count}), dir({file_path.encode(encoding="utf-8", errors="ignore").decode()})')
            extract_files(file_path, password_list, count)

        # 文件判断是否为压缩文件
        elif is_compressed(file_path):
            print(f'(loop:{count}), file_path({file_path.encode(encoding="utf-8", errors="ignore").decode()})')
            # 创建文件夹
            new_folder_name_list = file_name.split(".", 1)
            new_folder_path = os.path.join(folder, new_folder_name_list[0])
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            # 文件重命名,避免压缩文件与源文件同名时，出现系统占用
            new_file_path = file_path + '1'
            os.rename(file_path, new_file_path)
            for password in password_list:
                try:
                    # 开始解压
                    subprocess.check_output([exe_process, 'x', '-p' + password, '-o' + new_folder_path, '-y', new_file_path])
                    os.remove(new_file_path)
                    break
                except subprocess.CalledProcessError as e:
                    continue
            else:
                print(f'(loop:{count}), file_path({file_path})')
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
                    failed_files.append((file_name, 'Incorrect password'))

    with open(os.path.join(folder, 'failed_files.txt'), 'w', encoding='utf-8') as f:
        for file_name, reason in failed_files:
            f.write(f'{file_name}: {reason}\n')


passwords = []
exe_process = "7z"
password_file = 'passwords.txt'
dest_dir = '.'


if platform.system() == 'Windows':
    exe_process = '7z'
elif platform.system() == 'Linux':
    exe_process = '7zz'

# 调用函数进行文件读取和打印
read_passwords(password_file)
# 可能涉及多重解压，默认执行4次
for i in range(4):
    extract_files(dest_dir, passwords, i)
