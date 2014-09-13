RenderChan
==========

RenderChan is a smart rendering manager for animation projects. It takes a file for rendering  and analyses all its dependencies. If any of the dependent files needs to be rendered (or changed since the last rendering), then dependency is submitted for rendering together with an original file.

So, RenderChan constructs a list of tasks for rendering with consideration of changes in the project tree and existing renderings. The resulting list of tasks can be executed locally on the single machine or passed to renderfarm.

Currently following renderfarms supported:
 * CGRU/Afanasy (http://cgru.info/) - recommended
 * Puli (http://opensource.mikrosimage.eu/puli.html)

There's more detailed explanation of the concept here - http://www.youtube.com/watch?v=8EkQRLS9pN0 (Remake is an early prototype of RenderChan).﻿
