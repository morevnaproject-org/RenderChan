@echo off
set RENDERCHAN_ENVDIR=%~dp0\..\..\env
set PATH="%~dp0\..\..\python\";%PATH%
python "%~dp0\renderchan" %*
