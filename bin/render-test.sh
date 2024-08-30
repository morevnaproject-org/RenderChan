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

# shot 1, 43,46 background
./renderchan "../projects/Dystopia/extras/backgrounds/shot 1, 43, 46 rally crowd Background.psd" && cp "../projects/Dystopia/render/extras/backgrounds/shot 1, 43, 46 rally crowd Background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/shot 1, 43, 46 rally crowd Background.jpg"



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


# shot 10
./renderchan "../projects/Dystopia/inputs/shot 10/Shot 10.kra" && mkdir "../projects/Dystopia/scenes/shot 10" && cp -r "../projects/Dystopia/render/inputs/shot 10/Shot 10.kra.png" "../projects/Dystopia/scenes/shot 10"

# shot 10 tnz file

./renderchan "../projects/Dystopia/scenes/Shot 10.tnz"

# shot 11a
./renderchan "../projects/Dystopia/inputs/shot 11a/Shot 11a.kra" && mkdir "../projects/Dystopia/scenes/shot 11a" && cp -r "../projects/Dystopia/render/inputs/shot 11a/Shot 11a.kra.png" "../projects/Dystopia/scenes/shot 11a/"

# shot 11a toonz file
./renderchan "../projects/Dystopia/scenes/shot 11a.tnz"

# speedline effects
cp "../projects/Dystopia/extras/speedlines/speedlines.png" "../projects/Dystopia/scenes"

# shot 11b
./renderchan "../projects/Dystopia/inputs/shot 11b/Shot 11 animation B.kra" && mkdir "../projects/Dystopia/scenes/shot 11b" && cp -r "../projects/Dystopia/render/inputs/shot 11b/Shot 11 animation B.kra.png" "../projects/Dystopia/scenes/shot 11b"


#shot 11b tnz file
./renderchan "../projects/Dystopia/scenes/shot 11b.tnz"



# shot 14 Animation files
./renderchan "../projects/Dystopia/inputs/shot 14/Shot 14 Animation.kra"
cp -r "../projects/Dystopia/render/inputs/shot 14/Shot 14 Animation.kra.png" "../projects/Dystopia/scenes"

# shot 14 backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/Shot 14 Background.psd"

# shot 14 smoke fx
./renderchan "../projects/Dystopia/extras/smoke fx/igb_fx_coloured.kra"
cp -r "../projects/Dystopia/render/extras/smoke fx" "../projects/Dystopia/scenes"

cp "../projects/Dystopia/render/extras/backgrounds/Shot 14 Background.kra.png" "../projects/Dystopia/scenes/backgrounds/Shot 14 Background.png"

# shot 14 Toonz files
./renderchan "../projects/Dystopia/scenes/shot 14.tnz"


# shot 15 animation files
./renderchan "../projects/Dystopia/inputs/shot 15/Shot 15.kra"
 
cp -r "../projects/Dystopia/render/inputs/shot 15/Shot 15.kra.png" "../projects/Dystopia/scenes"

# shot 15 Toonz files
./renderchan "../projects/Dystopia/scenes/shot 15.tnz"

# shot 16 animation files
./renderchan "../projects/Dystopia/inputs/shot 16/Shot 16.kra"

cp -r "../projects/Dystopia/render/inputs/shot 16/Shot 16.kra.png" "../projects/Dystopia/scenes"

# shot 16 backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/Shot 16 background.psd"
cp "../projects/Dystopia/render/extras/backgrounds/Shot 16 background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/Shot 16 background.jpg"

# shot 16 Toonz files
./renderchan "../projects/Dystopia/scenes/shot 16.tnz"

# shot 17 animation files
./renderchan "../projects/Dystopia/inputs/shot 17/shot 17 V-shot.kra"
mkdir "../projects/Dystopia/scenes/shot 17"
cp "../projects/Dystopia/render/inputs/shot 17/shot 17 V-shot.kra.png" "../projects/Dystopia/scenes/shot 17/shot 17 V-shot.png"


# shot 17 smoke fx
./renderchan "../projects/Dystopia/extras/smoke fx/smoke_3.kra"
cp -r "../projects/Dystopia/render/extras/smoke fx" "../projects/Dystopia/scenes"


# shot 17 Toonz file
./renderchan "../projects/Dystopia/scenes/shot 17.tnz"

# shot 18 animation files
./renderchan "../projects/Dystopia/inputs/shot 18/Shot 18.psd"
mkdir "../projects/Dystopia/scenes/shot 18"
cp "../projects/Dystopia/render/inputs/shot 18/Shot 18.psd.png" "../projects/Dystopia/scenes/shot 18/Shot 18.png"

# shot 18 smoke fx
./renderchan "../projects/Dystopia/extras/smoke fx/smoke_1.kra" &&
cp -r "../projects/Dystopia/render/extras/smoke fx" "../projects/Dystopia/scenes"


# shot 18 toonz files
./renderchan "../projects/Dystopia/scenes/shot 18.tnz"

# shot 19 animation files
./renderchan "../projects/Dystopia/inputs/shot 19/Shot 19 animation.kra"
cp -r "../projects/Dystopia/render/inputs/shot 19/Shot 19 animation.kra.png" "../projects/Dystopia/scenes"


# shot 19 toonz file
./renderchan "../projects/Dystopia/scenes/shot 19.tnz"

# SHot 20 Animation Files
# shot 20 combines with shot 19 for render
./renderchan "../projects/Dystopia/inputs/shot 20/Shot 20.psd" 
mkdir "../projects/Dystopia/scenes/shot 20"
cp "../projects/Dystopia/render/inputs/shot 20/Shot 20.psd.png" "../projects/Dystopia/scenes/shot 20/Shot 20.png"


# shot 23 animation files
./renderchan "../projects/Dystopia/inputs/shot 23/shot 23.kra"

cp -r "../projects/Dystopia/render/inputs/shot 23/shot 23.kra.png"  "../projects/Dystopia/scenes"


# shot 23 Toons files
./renderchan "../projects/Dystopia/scenes/Shot 23.tnz"

# shot 24 animation files

./renderchan "../projects/Dystopia/inputs/shot 24/shot 24 animation.kra"
cp -r "../projects/Dystopia/render/inputs/shot 24/shot 24 animation.kra.png" "../projects/Dystopia/scenes"


# shot 24 toonz files
./renderchan "../projects/Dystopia/scenes/shot 24.tnz"

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


#Sky Background
./renderchan "../projects/Dystopia/extras/backgrounds/sky.psd" && cp "../projects/Dystopia/render/extras/backgrounds/sky.psd.jpg" "../projects/Dystopia/scenes/backgrounds/sky.jpg"



# Shot 49
./renderchan "../projects/Dystopia/inputs/shot 49/shot 49.psd" && mkdir "../projects/Dystopia/scenes/shot 49" && cp "../projects/Dystopia/render/inputs/shot 49/shot 49.psd.png" "../projects/Dystopia/scenes/shot 49/shot 49.png" 

# shot 49 tnz file
./renderchan "../projects/Dystopia/scenes/shot 49.tnz"



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

# shot 60 Backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/shot 60 background.psd"

cp "../projects/Dystopia/render/extras/backgrounds/shot 60 background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/shot 60 background.jpg"

# shot 60 Dust Fx
./renderchan "../projects/Dystopia/extras/dust fx/dustfx.kra"

cp -r "../projects/Dystopia/render/extras/dust fx/dustfx.kra.png" "../projects/Dystopia/scenes"

# shot 71 animation files
./renderchan "../projects/Dystopia/inputs/shot 71/shot 71.kra" && cp -r "../projects/Dystopia/render/inputs/shot 71/shot 71.kra.png" "../projects/Dystopia/scenes"



# shot 71 A animation files
# shots 71 and 71A are combined shots for render
./renderchan "../projects/Dystopia/inputs/shot 71A/bird_flight_coloured.kra" && cp -r "../projects/Dystopia/render/inputs/shot 71A" "../projects/Dystopia/scenes"



# shot 71 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 71.tnz"

# shot 72 animation files
./renderchan "../projects/Dystopia/inputs/shot 72/shot 72_Background.psd" && cp "../projects/Dystopia/render/inputs/shot 72/shot 72_Background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/shot 72_Background.jpg"  


# shot 72 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 72.tnz"

#shot 73 animation files
./renderchan "../projects/Dystopia/inputs/shot 73/shot 73.kra" && cp -r "../projects/Dystopia/render/inputs/shot 73/shot 73.kra.png" "../projects/Dystopia/scenes"

# shot 73 Backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/shot 73_background.psd" && cp "../projects/Dystopia/render/extras/backgrounds/shot 73_background.psd.jpg" "../projects/Dystopia/scenes/backgrounds/shot 73_background.jpg"


# shot 73 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 73.tnz"

# shot 74 animation files
./renderchan "../projects/Dystopia/inputs/shot 74/shot 74 animation.kra" && cp -r "../projects/Dystopia/render/inputs/shot 74/shot 74 animation.kra.png" "../projects/Dystopia/scenes"


#shot 74 toonz files
./renderchan "../projects/Dystopia/scenes/Shot 74.tnz"


#shot 100 animation files
./renderchan "../projects/Dystopia/inputs/shot 100/shot 100.psd"

mkdir "../projects/Dystopia/scenes/shot 100"
cp "../projects/Dystopia/render/inputs/shot 100/shot 100.psd.jpg" "../projects/Dystopia/scenes/shot 100/shot 100.jpg"

# shot 100 Toonz file
./renderchan "../projects/Dystopia/scenes/shot 100.tnz"


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
#./renderchan --profile hd "../projects/Dystopia/project.blend"

# Shorts Render for mobile
# for Youtube default (1080o) 

#ep 1
./renderchan --profile mobile "../projects/Dystopia/project.blend"

#ep 2 widescreen
./renderchan --profile youtube "../projects/Dystopia/project2.blend"


#ep 3 shorts
./renderchan --profile mobile "../projects/Dystopia/project3.blend"
