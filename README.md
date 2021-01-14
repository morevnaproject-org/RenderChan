RenderChan
==========

<img src="http://artwork.morevnaproject.org/albums/2016-06-13-renderchan-logo-v2/2016-06-13-logo-alpha.png" alt="RenderChan Logo" height=330 title="RenderChan mascot by Anastasia Majzhegisheva" />

RenderChan is a smart rendering manager for animation projects. It takes a file for rendering  and analyses all its dependencies. If any of the dependent files needs to be rendered (or changed since the last rendering), then dependency is submitted for rendering together with an original file.

So, RenderChan constructs a list of tasks for rendering with consideration of changes in the project tree and existing renderings. The resulting list of tasks can be executed locally on the single machine or passed to renderfarm (can work with CGRU/Afanasy renderfarm - http://cgru.info/).

Detailed explanation of the concept here - http://www.youtube.com/watch?v=8EkQRLS9pN0 (Remake is an early prototype of RenderChan).﻿
