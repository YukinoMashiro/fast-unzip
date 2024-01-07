import os
import subprocess
import platform
import hashlib
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import configparser
import json


class CMDApp:
    def __init__(self):
        # 实例化配置类
        self.configurator = Configurator()
        # 实例化解压类
        self.extractor = FileExtractor(self.configurator)
        # 实例化日志类
        self.logger = Logger()

    def read_config(self, file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                datas = json.load(f)
                return datas
        except FileNotFoundError:
            self.logger.log2both(logging.ERROR,
                                 f'Config file not found:{file}')
        except json.JSONDecodeError:
            self.logger.log2both(logging.ERROR,
                                 f'Config file format error:{file}')
        except Exception as e:
            self.logger.log2both(logging.ERROR,
                                 f'unknown error:{str(e)}')
        return None

    def load_config(self, file):
        config_key_exec_count = "exec_count"
        config_key_dest_dir = "dest_dir"
        config_key_ignore_format_exe = "ignore_format_exe"
        config_key_access_code = "access_code"
        config_key_password_list = "password_list"
        data = self.read_config(file)
        if data is not None:
            if config_key_exec_count in data:
                self.configurator.execution_count = data[config_key_exec_count]
            if config_key_dest_dir in data:
                self.configurator.decompress_path = data[config_key_dest_dir]
            if config_key_ignore_format_exe in data:
                self.configurator.ignore_exe = data[config_key_ignore_format_exe]
            if config_key_access_code in data:
                self.configurator.access_code = data[config_key_access_code]
            if config_key_password_list in data:
                self.configurator.password_list = data[config_key_password_list]
        else:
            self.logger.log2both(logging.INFO, 'use default config')

    def run(self):
        self.extractor.run()


class GUIApp:
    def __init__(self):
        self.password_file_path_entry = None
        self.key_entry = None
        self.ignore_exe_var = None
        self.execution_count_entry = None
        self.decompress_path_entry = None
        self.root = tk.Tk()
        self.root.title("参数配置")

        self.config = configparser.ConfigParser()
        self.config_file_path = "config.ini"

        self.load_config()

        self.create_widgets()

        # 实例化配置类
        self.configurator = Configurator()
        # 实例化解压类
        self.extractor = FileExtractor(self.configurator)

    def load_config(self):
        try:
            self.config.read(self.config_file_path)
            self.default_config = {
                "decompress_path": self.config.get("DEFAULT", "decompress_path", fallback=""),
                "execution_count": self.config.getint("DEFAULT", "execution_count", fallback=1),
                "ignore_exe": self.config.getboolean("DEFAULT", "ignore_exe", fallback=True),
                "key": self.config.get("DEFAULT", "key", fallback=""),
                "password_file_path": self.config.get("DEFAULT", "password_file_path", fallback="")
            }
        except configparser.Error:
            self.default_config = {}

    def save_config(self, data):
        self.config["DEFAULT"] = data
        with open(self.config_file_path, "w") as configfile:
            self.config.write(configfile)

    def select_directory(self, entry_widget):
        directory_path = filedialog.askdirectory()
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, directory_path)

    def select_file(self, entry_widget):
        file_path = filedialog.askopenfilename()
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)

    def create_widgets(self):
        # 解压路径
        decompress_path_label = tk.Label(self.root, text="解压路径:")
        decompress_path_label.grid(row=0, column=0, padx=5, pady=5)

        self.decompress_path_entry = tk.Entry(self.root)
        self.decompress_path_entry.insert(0, self.default_config.get("decompress_path", ""))
        self.decompress_path_entry.grid(row=0, column=1, padx=5, pady=5)

        decompress_path_button = tk.Button(self.root, text="选择路径",
                                           command=lambda: self.select_directory(self.decompress_path_entry))
        decompress_path_button.grid(row=0, column=2, padx=5, pady=5)

        # 执行次数
        execution_count_label = tk.Label(self.root, text="执行次数:")
        execution_count_label.grid(row=1, column=0, padx=5, pady=5)

        self.execution_count_entry = tk.Entry(self.root)
        self.execution_count_entry.insert(0, self.default_config.get("execution_count", ""))
        self.execution_count_entry.grid(row=1, column=1, padx=5, pady=5)

        # 是否忽略exe文件
        key_label = tk.Label(self.root, text="忽略exe:")
        key_label.grid(row=2, column=0, padx=5, pady=5)

        self.ignore_exe_var = tk.BooleanVar()
        ignore_exe_checkbox = tk.Checkbutton(self.root, variable=self.ignore_exe_var)
        ignore_exe_checkbox.grid(row=2, column=1, padx=5, pady=5)
        ignore_exe_checkbox.select() if self.default_config.get("ignore_exe", False) else ignore_exe_checkbox.deselect()

        # 密钥
        key_label = tk.Label(self.root, text="密钥:")
        key_label.grid(row=3, column=0, padx=5, pady=5)

        self.key_entry = tk.Entry(self.root, show="*")
        self.key_entry.insert(0, self.default_config.get("key", ""))
        self.key_entry.grid(row=3, column=1, padx=5, pady=5)

        # 预制密码文件路径
        password_file_path_label = tk.Label(self.root, text="预制密码文件路径:")
        password_file_path_label.grid(row=4, column=0, padx=5, pady=5)

        self.password_file_path_entry = tk.Entry(self.root)
        self.password_file_path_entry.insert(0, self.default_config.get("password_file_path", ""))
        self.password_file_path_entry.grid(row=4, column=1, padx=5, pady=5)

        password_file_path_button = tk.Button(self.root, text="选择路径",
                                              command=lambda: self.select_file(self.password_file_path_entry))
        password_file_path_button.grid(row=4, column=2, padx=5, pady=5)

        # 确认按钮
        confirm_button = tk.Button(self.root, text="确认", command=self.on_confirm)
        confirm_button.grid(row=5, column=0, columnspan=3, pady=10)

    def on_confirm(self):
        decompress_path = self.decompress_path_entry.get()
        execution_count = int(self.execution_count_entry.get())
        ignore_exe = self.ignore_exe_var.get()
        key = self.key_entry.get()
        password_file_path = self.password_file_path_entry.get()

        self.configurator.decompress_path = decompress_path
        self.configurator.execution_count = execution_count
        self.configurator.ignore_exe = ignore_exe
        self.configurator.access_code = key
        self.configurator.password_file_path = password_file_path
        self.configurator.get_password_list()

        print("解压路径:", decompress_path)
        print("执行次数:", execution_count)
        print("是否忽略exe文件:", ignore_exe)
        print("密钥:", key)
        print("预制密码文件路径:", password_file_path)

        self.save_config({
            "decompress_path": decompress_path,
            "execution_count": execution_count,
            "ignore_exe": ignore_exe,
            "key": key,
            "password_file_path": password_file_path
        })

        self.root.destroy()
        # 调用解压程序
        self.extractor.run()

    def run(self):
        self.root.mainloop()


class Logger:
    def __init__(self):
        self.log_file = "log.log"
        self.levelToName = {
            logging.CRITICAL: 'CRITICAL',
            logging.ERROR: 'ERROR',
            logging.WARNING: 'WARNING',
            logging.INFO: 'INFO',
            logging.DEBUG: 'DEBUG',
            logging.NOTSET: 'NOTSET',
        }
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(filename=self.log_file,
                            encoding='utf-8',
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def log2file(self, level, msg):
        logging.log(level, msg)

    def log2screen(self, level, msg):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'{current_time} - {self.levelToName[level]} - {msg}')

    def log2both(self, level, msg):
        self.log2file(level, msg)
        self.log2screen(level, msg)


class Accessor:
    def __init__(self):
        self.mac_list = []
        self.mac_hash = []
        self.salt = "+-*/"
        self.get_mac_address()

    def sha1_hash_string(self, input_string):
        sha1 = hashlib.sha1()
        sha1.update(input_string.encode('utf-8'))
        return sha1.hexdigest()

    def get_mac_address(self):
        # 获取本机的网卡列表
        mac_address_list = os.popen('ipconfig /all').read().split('\n\n')

        # 遍历网卡列表，找到对应IP地址的网卡并返回MAC地址
        for mac_address in mac_address_list:
            if '物理地址' in mac_address:
                mac = mac_address.split('物理地址')[1].strip()
                mac = mac.split('\n')[0][-17:].strip()
                self.mac_list.append(mac)
                self.mac_hash.append(self.sha1_hash_string(mac + self.salt))
            if 'Physical' in mac_address:
                mac = mac_address.split('Physical')[1].strip()
                mac = mac.split('\n')[0][-17:].strip()
                mac_address_list.append(mac)
                self.mac_hash.append(self.sha1_hash_string(mac + self.salt))


class Configurator:
    def __init__(self):
        self.config_file = "config.json"
        self.execution_count = 1
        self.decompress_path = '.'
        self.ignore_exe = True
        self.access_code = ""
        self.password_file_path = ""
        self.password_list = []
        self.logger = Logger()

    def get_password_list(self):
        if not self.password_file_path == "":
            try:
                self.password_list = [line.strip() for line in open(self.password_file_path, 'r', encoding='utf-8')]
            except UnicodeDecodeError as e:
                self.logger.log2both(logging.ERROR, f'Failed to read file({self.password_file_path}), please make sure '
                                                    f'the file is a text file.')
            except Exception as e:
                self.logger.log2both(logging.ERROR, f"Caught exception: {e}, file({self.password_file_path})")
        else:
            self.logger.log2both(logging.INFO, f"No password file specified.")


class FileExtractor:
    def __init__(self, configurator):
        self.configurator = configurator
        self.own_file_name1 = os.path.basename(__file__)
        self.own_file_name2 = self.own_file_name1.split(".")[0]
        self.exe_process = "7z"
        self.platform = platform.system()
        self.logger = Logger()
        self.accessor = Accessor()

    def is_compressed(self, file_path):
        if os.path.isdir(file_path):
            return False
        else:
            command = [self.exe_process, 'l', '-p12345', file_path]
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

    def extract_files(self, folder, password_list, count):
        failed_files = []

        for file_name in os.listdir(folder):
            try:
                file_path = os.path.join(folder, file_name)
                # 为了解决编码问题
                path = file_path.encode(encoding="utf-8", errors="ignore").decode()
                # 文件夹，递归处理
                if os.path.isdir(file_path):
                    self.logger.log2both(logging.INFO, f'(loop:{count}), dir({path})')

                    # windows打包程序和7z程序放在这里面，无需解压
                    if file_name == "_internal":
                        continue
                    self.extract_files(file_path, password_list, count)

                # 压缩文件
                elif self.is_compressed(file_path):
                    self.logger.log2both(logging.INFO, f'(loop:{count}), compressed_file_path({path})')
                    # 由于部分exe文件也是压缩包，此类文件不需要解压, 本程序也有可能是压缩包，跳过
                    if ((self.configurator.ignore_exe
                         and file_name.endswith(".exe"))
                            or self.own_file_name1 == file_name
                            or self.own_file_name2 == file_name or self.logger.log_file == file_name):
                        self.logger.log2both(logging.INFO, f'(loop:{count}), ignore compressed_file_path({path})')
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
                                [self.exe_process, 'x', '-p' + password, '-o' + new_folder_path, '-y', new_file_path])
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
                                    [self.exe_process, 'x', '-p' + password, '-o' + new_folder_path, '-y', file_path])
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
                self.logger.log2both(logging.ERROR, f'Capture error: {e}')
        # 记录解压失败原因
        if failed_files:
            with open(os.path.join(folder, 'failed_files.txt'), 'w', encoding='utf-8') as f:
                for file_name, reason in failed_files:
                    f.write(f'{file_name}: {reason}\n')

    def run(self):
        if self.platform == 'Windows':
            self.exe_process = '7z'
        elif self.platform == 'Linux':
            self.exe_process = '7zz'

        self.logger.log2both(logging.INFO, "Start to unzip.")

        is_access = True
        # 当前只支持windows才作校验
        if self.platform == 'Windows':
            # 校验准入码
            if self.configurator.access_code == "":
                is_access = False
                self.logger.log2both(logging.ERROR,
                                     "No access code, please fill in the access code in the configuration file. If "
                                     "you do not have an access code, please purchase it.")
            elif self.configurator.access_code not in self.accessor.mac_hash:
                is_access = False
                self.logger.log2both(logging.ERROR, "Access code error, please purchase access code.")

        if is_access:
            for i in range(self.configurator.execution_count):
                if self.configurator.decompress_path == "":
                    # 图形界面没有配置解压目录，默认为当前目录
                    self.configurator.decompress_path = "."
                self.extract_files(self.configurator.decompress_path, self.configurator.password_list, i)

        self.logger.log2both(logging.INFO, "End to unzip.")
        if platform.system() == 'Windows':
            os.system('pause')


if __name__ == "__main__":
    if platform.system() == 'Windows':
        app = GUIApp()
        app.run()
    elif platform.system() == 'Linux':
        app = CMDApp()
        app.run()
