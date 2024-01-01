@echo off
::程序打包
pyinstaller fast-unzip-all.py --noconfirm
::拷贝7z程序
set source_folder=7z
set dest_folder=dist\fast-unzip-all\_internal
md "%dest_folder%\%source_folder%"
xcopy /E /Y %source_folder% "%dest_folder%\%source_folder%"
::拷贝配置文件
set source_folder=config.json
set dest_folder=dist\fast-unzip-all
xcopy /Y %source_folder% "%dest_folder%"

:: 拷贝打包文件
set source_folder=dist\fast-unzip-all
set dest_folder=target
md %dest_folder%
xcopy /E /Y %source_folder% "%dest_folder%"
pause