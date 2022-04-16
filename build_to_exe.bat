#python setup.py install
#python setup.py py2exe
python setup_scum_tool_admin.py build
move .\build\exe.win-amd64-3.9\scum_tool_admin.ico .\build\exe.win-amd64-3.9\lib\
xcopy  /E /H /C /I ressources\ build\exe.win-amd64-3.9\ressources
mkdir .\build\exe.win-amd64-3.9\config\
copy .\config\config.ini .\build\exe.win-amd64-3.9\config\config.ini
pause