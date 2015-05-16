SETLOCAL

REM variables
set original_directory="%cd%"
cd ..
set PYTHONPATH=%cd%

if "%1"=="r" goto:run

REM build
mkdir build\built
cd build\built
cmake -D BUILD_SHARED_LIBS=ON -D CMAKE_BUILD_TYPE=Release ..
if %ERRORLEVEL% NEQ 0 goto:end
call vcvarsall
msbuild /p:Configuration=Release Project.sln
if %ERRORLEVEL% NEQ 0 goto:end
cd ..\..

:run
cd build\built\Release
python -i ..\..\..\test\test.py

:end
cd %original_directory%

ENDLOCAL
