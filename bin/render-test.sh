./renderchan '../projects/Dystopia/inputs/shot 1/shot 1 frame by frame .kra' && cp -r "../projects/Dystopia/render/inputs/shot 1/shot 1 frame by frame .kra.png/" "../projects/Dystopia/scenes/"


./renderchan '../projects/Dystopia/extras/Truck 1/Truck.kra' && cp -r "../projects/Dystopia/render/extras/Truck 1" "../projects/Dystopia/scenes/" 


./renderchan "../projects/Dystopia/scenes/Shot 1.tnz"

./renderchan "../projects/Dystopia/project.blend"
