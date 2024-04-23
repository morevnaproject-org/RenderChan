#!/bin/bash

# Episode 1 Video Script

# To DO: Makse Scenes folder path en env variable

# Fx
# wind fx
./renderchan "../projects/Dystopia/extras/wind/wind fx.kra" && cp -r "../projects/Dystopia/render/extras/wind/wind fx.kra.png/" "../projects/Dystopia/scenes/" 


# Shot 0 Props
./renderchan "../projects/Dystopia/extras/earth/earth.kra" && cp  -r "../projects/Dystopia/render/extras/earth" "../projects/Dystopia/scenes/"


# Shot 0 Scene
./renderchan "../projects/Dystopia/scenes/shot 0.tnz"


# Shot 1 frames
./renderchan '../projects/Dystopia/inputs/shot 1/shot 1 frame by frame .kra' && cp -r "../projects/Dystopia/render/inputs/shot 1/shot 1 frame by frame .kra.png/" "../projects/Dystopia/scenes/"

# Shot 1 Props
./renderchan '../projects/Dystopia/extras/Truck 1/Truck.kra' && cp -r "../projects/Dystopia/render/extras/Truck 1" "../projects/Dystopia/scenes/" 


# Shot 1 Backgrounds
# Desert Bckground
# make background file and rename background image file
echo "Desert Background"
./renderchan "../projects/Dystopia/extras/backgrounds/raw 3 Dystopia Bckgrnd-1.psd" && mkdir "../projects/Dystopia/scenes/backgrounds"

mv "../projects/Dystopia/render/extras/backgrounds/raw 3 Dystopia Bckgrnd-1.psd.jpg" "../projects/Dystopia/scenes/backgrounds/raw 3 Dystopia Bckgrnd-1.jpg"

echo "Market Background"
# market background
./renderchan "../projects/Dystopia/extras/backgrounds/Market background.psd" && cp "../projects/Dystopia/render/extras/backgrounds/Market background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/Market background.jpg"




# copy background recursively (Depreciated)
#cp -r "../projects/Dystopia/render/extras/backgrounds" "../projects/Dystopia/scenes/"

	


# Shot 1 Scene
./renderchan "../projects/Dystopia/scenes/Shot 1.tnz"



#shot 3 props
#man & cow
echo "Man and Cow"
./renderchan "../projects/Dystopia/inputs/shot 3/shot 3.kra" && cp -r "../projects/Dystopia/render/inputs/shot 3/shot 3.kra.png/" "../projects/Dystopia/scenes/"


# shot 3 tnz files
./renderchan "../projects/Dystopia/scenes/Shot 3.tnz"


# Shot 4 Frames
./renderchan "../projects/Dystopia/inputs/shot 4/shot 4 crowd animation.kra"
./renderchan "../projects/Dystopia/inputs/shot 4/shot 4 crowd 2 animation.kra"
cp -r "../projects/Dystopia/render/inputs/shot 4/shot 4 crowd animation.kra.png/" "../projects/Dystopia/scenes/"
cp -r "../projects/Dystopia/render/inputs/shot 4/shot 4 crowd 2 animation.kra.png/" "../projects/Dystopia/scenes/"

# Shot 4 Background
./renderchan "../projects/Dystopia/extras/backgrounds/shot 4 Background.psd" && cp "../projects/Dystopia/render/extras/backgrounds/shot 4 Background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/shot 4 Background.jpg"

# Shot 4 Lights & Shadows
./renderchan "../projects/Dystopia/extras/lighting/lights.kra" && cp -r "../projects/Dystopia/render/extras/lighting/lights.kra.png" "../projects/Dystopia/scenes/"

# Shot 4 Toonz Files
./renderchan "../projects/Dystopia/scenes/Shot 4.tnz"

# Shot 5 Frames
./renderchan "../projects/Dystopia/inputs/shot 5/shot 5  animation fbf .kra" && cp -r "../projects/Dystopia/render/inputs/shot 5/shot 5  animation fbf .kra.png/" "../projects/Dystopia/scenes/"

#Shot 5 Tnz files
./renderchan "../projects/Dystopia/scenes/Shot 5.tnz"


#Shot 6 Frames
./renderchan "../projects/Dystopia/inputs/shot 6/shot 6 animation fbf.kra" && cp -r "../projects/Dystopia/render/inputs/shot 6/shot 6 animation fbf.kra.png" "../projects/Dystopia/scenes/"

#shot 6 Backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/Background and foreground assets shot  6.psd" && cp "../projects/Dystopia/render/extras/backgrounds/Background and foreground assets shot  6.psd.jpg" "../projects/Dystopia/scenes/backgrounds/Background and foreground assets shot  6.jpg"

#shot 6 fx
#rain fx
./renderchan "../projects/Dystopia/extras/rain/rain fx.kra" && cp -r "../projects/Dystopia/render/extras/rain/rain fx.kra.png" "../projects/Dystopia/scenes/"

# Shot 6 Toonz files
./renderchan "../projects/Dystopia/scenes/shot 6.tnz"

#shot 7 3D Background
./renderchan "../projects/Dystopia/extras/3D/corporate-building-interior.blend" && cp -r "../projects/Dystopia/render/extras/3D/corporate-building-interior.blend.png" "../projects/Dystopia/scenes/"

#shot 7 animation files
./renderchan "../projects/Dystopia/inputs/shot 7/shot 7 animation.kra" && cp -r "../projects/Dystopia/render/inputs/shot 7/shot 7 animation.kra.png" "../projects/Dystopia/scenes/"

# shot 7 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 7.tnz"


# Shot 8 Background
./renderchan "../projects/extras/Dystopia/backgrounds/Background 004.psd" && cp "../projects/Dystopia/render/extras/backgrounds/Background 004.psd.jpg" "../projects/Dystopia/scenes/backgrounds/Background 004.jpg"

# Shot 8 Animation rig files
./renderchan "../projects/Dystopia/inputs/shot 8/Shot 8.kra" && cp -r "../projects/Dystopia/render/inputs/shot 8/Shot 8.kra.png" "../projects/Dystopia/scenes/"

# Shot 8 fx : Pew Pew
./renderchan "../projects/Dystopia/extras/pew pew/pewpew.kra" && cp -r "../projects/Dystopia/render/extras/pew pew/pewpew.kra.png" "../projects/Dystopia/scenes/"


# shot 8 toonz files
./renderchan "../projects/Dystopia/scenes/shot 8.tnz"

# Shot 9 Mask
./renderchan "../projects/Dystopia/inputs/shot 9/mask.psd" 

# Shot 9 eyes fbf
./renderchan "../projects/Dystopia/inputs/shot 9/eyes coloured.kra" && cp -r "../projects/Dystopia/render/inputs/shot 9" "../projects/Dystopia/scenes"

cp "../projects/Dystopia/scenes/shot 9/mask.psd.jpg" "../projects/Dystopia/scenes/shot 9/mask.jpg"

# shot 9 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 9.tnz"


# SHot 20 Animation Files
./renderchan "../projects/Dystopia/inputs/shot 20/Shot 20.psd" 
mkdir "../projects/Dystopia/scenes/shot 20"
cp "../projects/Dystopia/render/inputs/shot 20/Shot 20.psd.png" "../projects/Dystopia/scenes/shot 20/Shot 20.png"

# Shot 39
./renderchan "../projects/Dystopia/inputs/shot 39/shot 39 background.psd"
./renderchan "../projects/Dystopia/inputs/shot 39/man 2 animation_2.kra"
./renderchan "../projects/Dystopia/inputs/shot 39/man 1.psd"

cp -r "../projects/Dystopia/render/inputs/shot 39" "../projects/Dystopia/scenes"
cp "../projects/Dystopia/render/inputs/shot 39/shot 39 background.psd.jpg" "../projects/Dystopia/scenes/shot 39/shot 39 background.jpg"

# shot 39 Blast & smoke fx
./renderchan "../projects/Dystopia/extras/Blast fx/Blast & smoke fx.kra" && cp -r "../projects/Dystopia/render/extras/Blast fx/Blast & smoke fx.kra.png" "../projects/Dystopia/scenes/"


# shot 39 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 39.tnz"
./renderchan "../projects/Dystopia/scenes/Shot 39_1.tnz"
# shot 50
./renderchan "../projects/Dystopia/inputs/shot 50/shot 50 animation.kra" 
#mkdir "../projects/Dystopia/scenes/shot 50"
cp -r "../projects/Dystopia/render/inputs/shot 50/shot 50 animation.kra.png" "../projects/Dystopia/scenes/"
./renderchan "../projects/Dystopia/scenes/shot 50.tnz"

# Spaceship extras
./renderchan "../projects/Dystopia/extras/spaceships/spaceships.kra" && cp -r "../projects/Dystopia/render/extras/spaceships" "../projects/Dystopia/scenes/"

# Shot 55
./renderchan "../projects/Dystopia/inputs/shot 55/shot 55.psd" && mkdir "../projects/Dystopia/scenes/shot 55" && cp "../projects/Dystopia/render/inputs/shot 55/shot 55.psd.png" "../projects/Dystopia/scenes/shot 55/shot 55.png"

# shot 55 toonz files
./renderchan "../projects/Dystopia/scenes/shot 55.tnz"

# Shot 56 Animation files

./renderchan "../projects/Dystopia/inputs/shot 56/shot 56.kra" && cp -r "../projects/Dystopia/render/inputs/shot 56/shot 56.kra.png" "../projects/Dystopia/scenes/"


# shot 56 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 56.tnz"

# Shot 57 animation files
./renderchan "../projects/Dystopia/inputs/shot 57/shot 57.psd" && mkdir "../projects/Dystopia/scenes/shot 57/" && cp "../projects/Dystopia/render/inputs/shot 57/shot 57.psd.png" "../projects/Dystopia/scenes/shot 57/shot 57.png"


# SHot 57 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 57.tnz"

# Shot 58
./renderchan "../projects/Dystopia/inputs/shot 58/shot 58.psd" && mkdir "../projects/Dystopia/scenes/shot 58/" && cp "../projects/Dystopia/render/inputs/shot 58/shot 58.psd.png" "../projects/Dystopia/scenes/shot 58/shot 58.png"


# Shot 58 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 58.tnz"


# Spritesheets
./renderchan "../projects/Dystopia/extras/spritesheets/spritesheet.kra" && cp -r "../projects/Dystopia/render/extras/spritesheets/spritesheet.kra.png" "../projects/Dystopia/scenes/"


# Animated Title
./renderchan "../projects/Dystopia/extras/animated title/animated title.kra" && cp -r "../projects/Dystopia/render/extras/animated title/animated title.kra.png/" "../projects/Dystopia/scenes/"




# animated title toonz files
./renderchan "../projects/Dystopia/scenes/title animation.tnz"



# credits source
./renderchan "../projects/Dystopia/extras/credits/credits.psd" && cp "../projects/Dystopia/render/extras/credits/credits.psd.png" "../projects/Dystopia/scenes/backgrounds/credits.png"

# credits render
./renderchan "../projects/Dystopia/scenes/credits.tnz"


# Widescreen Render
./renderchan --profile hd "../projects/Dystopia/project.blend"

# Shorts Render
./renderchan --profile mobile "../projects/Dystopia/project.blend"
