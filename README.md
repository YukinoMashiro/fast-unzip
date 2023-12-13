# fast-unzip
```bash
# 打包
pyinstaller fast-unzip-all.py --noconfirm
```
## 使用说明
`config.json`为配置文件
其中，
``exec_count``属性表示解压次数，默认为1
``dest_dir``属性表示待解压路径，请填写绝对路径，如果填写`.`表示解压当前路径，默认为当前路径
``password_list``表示预置密码列表，程序会尝试按照预置尝试解压，默认为无密码
```json
{
	"exec_count": 4,
	"dest_dir": ".",
	"password_list": ["password", "密码", "パスワード"]
}
```
如果`config.json`文件不存在，所有属性均按照默认值
## 注意
可执行文件，包含windows的exe文件和Linux的可执行二进制文件，可能为压缩文件，程序自动会过滤掉exe文件不做处理，Linux的可执行二进制文件无后缀，无法做判断，因此会直接进行解压，如果不需要，请手动移除。
