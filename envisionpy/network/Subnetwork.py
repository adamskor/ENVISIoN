import inviwopy
import numpy as np
import h5py
from envisionpy.utils.exceptions import *
import inviwopy.glm as glm

class Subnetwork():
    def __init__(self, inviwoApp):
        self.app = inviwoApp
        self.network = inviwoApp.network
        self.processors = {}
        self.image_outport = None


    def add_processor(self, id, name, xpos=0, ypos=0):
        factory = self.app.processorFactory
        new_processor = factory.create(id, glm.ivec2(xpos*25, ypos*25))
        new_processor.identifier = name
        self.network.addProcessor(new_processor)

        self.processors[name] = new_processor
        return new_processor

    def remove_processor(self, id):
        self.network.removeProcessor(self.processors[id])
        del self.processors[id]

    def remove_processor_by_ref(self, processor):
            self.network.removeProcessor(processor)
            self.processors = {key:val for key, val in self.processors.items() if val != processor}

    def get_processor(self, id):
        if id in self.processors:
            return self.processors[id]
        raise ProcessorNotFoundError("Processor with ID " + id + " not found.")

    def clear_processors(self):
    # Remove all the processors associated with this manager.
        for id in tuple(self.processors):
            self.remove_processor(id)

    def connect_image(self, image_inport):
        print(self.image_outport)
        self.network.addConnection(self.image_outport, image_inport)