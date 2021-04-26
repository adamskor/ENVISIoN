import inviwopy
import numpy as np
import h5py
from envisionpy.utils.exceptions import *
from envisionpy.utils.atomData import atomic_radii, element_names, element_colors
from .baseNetworks.Decoration import Decoration

class MolecularDynamics(Decoration):
    '''
    Manages a subnetwork for animation of molecular dynamics.

    arguments:
    inviwoApp:  ##Vad är detta?##
    hdf5_path: Path to hdf5-file.
    hdf5_output: The outport of the hdf5Source-processor. This processor is initialized in VisualisationManager.py
    xpos: The x-position of the processors in the inviwo network editor
    ypos: The y-position of the processors in the inviwo network editor

    setup_network: Function for creating the processornetwork.
    set_atom_radius: Sets the atom radius for the visualisation.
    '''
    def __init__(self, inviwoApp, hdf5_path, hdf5_output, xpos=0, ypos=0, inviwo = False):
        Decoration.__init__(self,inviwoApp)
        self.atom_radii = []
        self.atom_names = []
        self.nAtomTypes = 0
        self.inviwo = inviwo
        self.setup_network(hdf5_path, hdf5_output, xpos, ypos)
        if inviwo:
            self.set_atom_radius(0.12)
        self.toggle_full_mesh(True)
        self.hide()

    @staticmethod
    def valid_hdf5(hdf5_file):
        #Test if the MD-section of the hdf5 file is empty.
        #Returns True if the MD-section of the hdf5 file is not empty.
        return hdf5_file.get("MD") != None        #Kolla närmare på formatet för HDF5-filer. Detta verkar orsaka problem

    def get_ui_data(self):
        #Return a list of data to show on the user interface.
        return [
            self.atom_names,
            self.atom_radii
        ]

    def valid_visualisations(self):
        #Return a list of valid decorations.
        return ['charge', 'elf', 'parchg']

    def connect_decoration(self, other, vis_type):
        # Connect properties and ports between visualisations.
        if vis_type not in self.valid_decorations():
            raise EnvisionError('Invalid decoration type ['+vis_type+'].')

        self.other_subnetworks[vis_type] = otherwise

        #Link needed properties between networks.
        if vis_type == 'molecular_dynamics':
            self.network.addLink(other.camera_prop, self.camera_prop)
            self.network.addLink(self.camera_prop, other.camera_prop)
            other.camera_prop.invalidate()

        other.connect_decoration_ports(self.decoration_outport)

    def disconnect_decoration(self, other, vis_type):
        # Disconnect properties and ports between visualisations.
        if vis_type == 'molecular_dynamics':
            self.network.removeLink(self.camera_prop, other.camera_prop)
        other.disconnect_decorations_port(self.decoration_outport)

    def show(self):
        #Shows the visualisation in the canvas
        self.get_processor('UnitcellCanvas').widget.show()

    def hide(self):
        #Hides the visualisation in the canvas
        self.get_processor('UnitcellCanvas').widget.hide()

# ------------------------------------------
# ------- Property control functions -------

    def set_atom_radius(self, radius, index=None):
        structureMesh = self.get_processor('UnitcellMesh')
        if structureMesh.fullMesh.value:
            if index != None:
                self.atom_radii[index] = radius
                structureMesh.getPropertyByIdentifier("radius" + str(index)).value = radius
            else:
                for i in range(self.nAtomTypes):
                    self.atom_radii[i] = radius
                    self.set_atom_radius(radius, i)
        else:
            #Sets the radius of the atoms.
            sphereRenderer = self.get_processor('UnitcellRenderer')
            sphereRenderer.sphereProperties.defaultRadius.value = radius
            print(range(self.nAtomTypes))
            counter = 0
            while counter < self.nAtomTypes:
                self.atom_radii += [radius]
                counter += 1
            #for i in range(self.nAtomTypes):
            #    print(i)
            #    self.atom_radii[i] += [radius]

    def hide_atoms(self):
        #Sets the atom radiuses to 0.
        return self.set_atom_radius(0)

    def toggle_full_mesh(self, enable):
        structMesh = self.get_processor('UnitcellMesh')
        structMesh.fullMesh.value = enable

    def set_canvas_position(self, x, y):
        #Uppdates the position of the canvas
        #Upper left corner will be at coordinate (x,y)
            unitcellCanvas = self.get_processor('UnitcellMesh')
            unitcellCanvas.position.value = inviwopy.glm.ivec2(x, y)

# ------------------------------------------
# ------- Network building functions -------

    def setup_network(self, hdf5_path, hdf5_output, xpos, ypos):
        #Add processors.
        #Property animator is the processor which changes the properties of the coordinate-reader.
        strucMesh = self.add_processor('envision.StructureMesh', 'UnitcellMesh', xpos, ypos+3)
        meshRender = self.add_processor('org.inviwo.SphereRenderer', 'UnitcellRenderer', xpos, ypos+6)
        background = self.add_processor('org.inviwo.Background', 'AtomBackground', xpos, ypos+9)
        canvas = self.add_processor('org.inviwo.CanvasGL', 'UnitcellCanvas', xpos, ypos+12)
        propertyAnimator = self.add_processor('org.inviwo.OrdinalPropertyAnimator', 'Animator', xpos+7, ypos+3)

        #selectedIndex chooses which type of property to create.
        #Index 8 is for the property "Int", an integer.
        propertyAnimator.property.selectedIndex = 8

        #add.press() presses the add button. This creates the Int-property.
        propertyAnimator.add.press()

        #delta.value changes how fast the animation is rendered.
        propertyAnimator.Int.delta.value = 1

        #Sets Int to be periodic.
        propertyAnimator.Int.boundary.selectedIndex = 1


        canvas.inputSize.dimensions.value = inviwopy.glm.size2_t(500, 500)

        #Connect processors
        self.network.addConnection(strucMesh.getOutport('mesh'), meshRender.getInport('geometry'))
        self.network.addConnection(meshRender.getOutport('image'), background.getInport('inport'))
        self.network.addConnection(background.getOutport('outport'), canvas.getInport('inport'))


        with h5py.File(hdf5_path, "r") as h5:
            # Set basis matrix and scaling
            strucMesh.basis.value = inviwopy.glm.mat3(
                1, 0, 0,
                0, 1, 0,
                0, 0, 1)

            MD_group = "/MD"

            #Sets the boundarys of the value of Int. This repressents the
            #number of timesteps in the animation. The HDF5-file starts the
            #timestep indexing at 0, so maxValue is set to the number
            #of timesteps - 1.
            propertyAnimator.Int.value.minValue = 0
            propertyAnimator.Int.value.maxValue = len(list(h5[MD_group + "/Atoms"].keys())) - 1

            #Loops through all different types of atoms.
            #Key: atom type i.e. "Fe" or "Al"

        #    if self.inviwo:
            for i, key in enumerate(list(h5[MD_group + "/Atoms/0000"].keys())):

                    #----------
                    # element = h5[MD_group + "/Atoms/"+key].attrs['element']
                    # name = element_names.get(element, 'Unknown')
                    # color = element_colors.get(element, (0.5, 0.5, 0.5, 0.5))
                    # radius = atomic_radii.get(element, 0.5)
                    # self.atom_names.append(name)
                    # self.atom_radii.append(radius)
                element = h5[MD_group + "/Atoms/0000/"+key].attrs['element']

                name = element_names.get(element, 'Unknown')
                color = element_colors.get(element, (0.5, 0.5, 0.5, 1.0))
                radius = atomic_radii.get(element, 0.5)
                self.atom_names.append(name)
                self.atom_radii.append(radius)
                y = list(color)
                y[3] = 0.7
                color = tuple(y)
                coordReader = self.add_processor('envision.CoordinateReader', '{0} {1}'.format(0, key), xpos-i*7, ypos)
                self.network.addConnection(hdf5_output, coordReader.getInport('inport'))
                self.network.addConnection(coordReader.getOutport('outport'), strucMesh.getInport('coordinates'))
                self.network.addLink(propertyAnimator.Int.value, coordReader.timestep)
                coordReader.path.value = MD_group + '/Atoms/0000/' + key
                if strucMesh.getPropertyByIdentifier('radius{0}'.format(i)) == None:
                        continue
                strucMesh_radius_property = strucMesh.getPropertyByIdentifier('radius{0}'.format(i))

                strucMesh_radius_property.maxValue = 10
                print(radius)
                strucMesh_radius_property.value = radius/30
                strucMesh_color_property = strucMesh.getPropertyByIdentifier('color{0}'.format(i))
                strucMesh_color_property.value = inviwopy.glm.vec4(color[0],color[1],color[2],color[3])

                strucMesh_atom_property = strucMesh.getPropertyByIdentifier('atoms{0}'.format(i))
                strucMesh_atom_property.value = 0
                strucMesh_atom_property.minValue = 0
                strucMesh_atom_property.maxValue = 0


                    #Ersätt sträng i coordReader till variablen name när giltig name finns
                #    coordReader = self.add_processor('envision.CoordinateReader', '{0} {1}'.format(0, key), xpos-i*7, ypos)
                self.network.addConnection(hdf5_output, coordReader.getInport('inport'))
                self.network.addConnection(coordReader.getOutport('outport'), strucMesh.getInport('coordinates'))

                    #Links the Int-value of propertyAnimator to the timestep-variable
                    #for coordinatereader. This will make the coordinatereader loop
                    #throught the timesteps of the HDF5-file.
                self.network.addLink(propertyAnimator.Int.value, coordReader.timestep)

                #    coordReader.path.value = MD_group + '/Atoms/0000/' + key

                    #----------
                    # if strucMesh.getPropertyByIdentifier('radius{0}'.format(i)) == None:
                    #         continue
                    # strucMesh_radius_property = strucMesh.getPropertyByIdentifier('radius{0}'.format(i))
                    # strucMesh_radius_property.maxValue = 10
                    # strucMesh_radius_property.minValue = 0.001
                    # strucMesh_radius_property.value = 0.5
                    #
                    # strucMesh_color_property = strucMesh.getPropertyByIdentifier('color{0}'.format(i))
                    # strucMesh_color_property.value = inviwopy.glm.vec4(color[0],color[1],color[2],color[3])
                    #
                    # strucMesh_atom_property = strucMesh.getPropertyByIdentifier('atoms{0}'.format(i))
                    # print('atoms{0}'.format(i))
                    # strucMesh_atom_property.value = 0
                    # strucMesh_atom_property.minValue = 0
                    # strucMesh_atom_property.maxValue = 0
                    #----------

                self.nAtomTypes += 1

                #else:
                    # atomRenderer = self.add_processor('org.inviwo.GeometryRenderGL', 'AtomRenderer', xpos+7, ypos+9)
                    # self.network.removeConnection(meshRenderer.getOutport('image'), background.getInport('inport'))
                    # self.network.addLink(propertyAnimator.Int.value, atomRenderer.timestep)
                    #
                    # self.network.addConnection(atomRenderer.getOutport('image'),background.getInport('inport'))
                    # self.network.addLink(atomRenderer.camera, meshRenderer.camera)
                    # self.network.addLink(meshRenderer.camera, atomRenderer.camera)
                    # for i,key in enumerate(list(h5[MD_group + "/Atoms/0000/"].keys())):
                    #     element = h5[base_group + "/Atoms/0000/"+key].attrs['element']
                    #     color = element_colors.get(element, (0.5, 0.5, 0.5, 1.0))
                    #     radius = atomic_radii.get(element, 0.5)
                    #     for p,n in enumerate(h5[base_group + "/Atoms/0000/"+key]):
                    #         meshCreate = self.add_processor('org.inviwo.MeshCreator', '{0} {1} {2}'.format(p, i, "boll"), xpos, ypos)
                    #         self.network.addConnection(meshCreate.getOutport('outport'), atomRenderer.getInport('geometry'))
                    #         self.network.addLink(meshCreate.camera, meshRenderer.camera)
                    #         self.network.addLink(meshRenderer.camera, meshCreate.camera)
                    #         meshCreate.meshType.selectedIndex = 13
                    #         meshCreate.scale.value = radius/30
                    #         meshCreate.color.value = inviwopy.glm.vec4(color[0],color[1],color[2],0.7)
                    #         meshCreate.position1.value = inviwopy.glm.vec3(n[0]-0.5, n[1]-0.5, n[2]-0.5)


        #Presses the play-button for the Int-value of propertyAnimator.
        #This initiates the animation.
        propertyAnimator.play.press()


        self.decoration_outport = meshRender.getOutport('image')
        self.decoration_inport = meshRender.getInport('imageInport')
        self.camera_prop = meshRender.camera
