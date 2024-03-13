# Shot 1 frames
./renderchan '../projects/Dystopia/inputs/shot 1/shot 1 frame by frame .kra' && cp -r "../projects/Dystopia/render/inputs/shot 1/shot 1 frame by frame .kra.png/" "../projects/Dystopia/scenes/"

# SHot 1 Props
./renderchan '../projects/Dystopia/extras/Truck 1/Truck.kra' && cp -r "../projects/Dystopia/render/extras/Truck 1" "../projects/Dystopia/scenes/" 

# Backgrounds
./renderchan "../projects/Dystopia/extras/backgrounds/raw 3 Dystopia Bckgrnd-1.psd"

# Shot 1 Scene
./renderchan "../projects/Dystopia/scenes/Shot 1.tnz"

./renderchan "../projects/Dystopia/project.blend"
