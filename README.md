RenderChan
==========

<img src="http://artwork.morevnaproject.org/albums/2016-06-13-renderchan-logo-v2/2016-06-13-logo-alpha.png" alt="RenderChan Logo" height=330 title="RenderChan mascot by Anastasia Majzhegisheva" />

RenderChan is a smart rendering manager for animation projects. It takes a file for rendering  and analyses all its dependencies. If any of the dependent files needs to be rendered (or changed since the last rendering), then dependency is submitted for rendering together with an original file.

So, RenderChan constructs a list of tasks for rendering with consideration of changes in the project tree and existing renderings. The resulting list of tasks can be executed locally on the single machine or passed to renderfarm (can work with CGRU/Afanasy renderfarm - http://cgru.info/).

Detailed explanation of the concept here - http://www.youtube.com/watch?v=8EkQRLS9pN0 (Remake is an early prototype of RenderChan).﻿


## Linux Install & Use
**(1) clone repository**


**(2) Run "$nano /etc/environment" and add the following text to the file RENDERCHAN_ENVDIR="/home/your_pc/renderchan/env/linux"
    to create an environment variable for Opentoonz**

    
**(3) Download Latest Opentoonz app image binary and place in "/home/your_pc/renderchan/env/linux" folder**


**(4) Create A tcomposer.txt file in this linux directory and add the name of your Opentoonz app image binary like
    OpenToonz-1.4.0-morevna-2020.06.14-linux64-b6177.appimage**


**(5) cd ../..**


**(6) cd bin**


**(7) Run $./renderchan '/path_to_file/' to Render**

## Additional Steps

**(8) create .conf files :** 
    create .conf files for each Animation source file (.kra, .tnz,.blend) to finetune rendering parameters
    e.g. project.blend will have project.blend.conf files; shot1.kra would have shot1.kra.conf
    as a configuration file
 
