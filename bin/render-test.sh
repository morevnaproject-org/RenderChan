#!/bin/bash

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


# Widescreen Render
./renderchan --profile hd "../projects/Dystopia/project.blend"

# Shorts Render
./renderchan --profile mobile "../projects/Dystopia/project.blend"
