/*********************************************************************************
 *
 * Copyright (c) 2017-2021 Josef Adamsson, Gabriel Anderberg, Didrik Axén,
 * Adam Engman, Kristoffer Gubberud Maras, Joakim Stenborg
 * Inviwo - Interactive Visualization Workshop
 *
 * Copyright (c) 2017 Inviwo Foundation
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 *********************************************************************************
 *  Alterations to this file by Gabriel Anderberg, Didrik Axén,
 *  Adam Engman, Kristoffer Gubberud Maras, Joakim Stenborg
 *
 *  To the extent possible under law, the person who associated CC0 with
 *  the alterations to this file has waived all copyright and related
 *  or neighboring rights to the alterations made to this file.
 *
 *  You should have received a copy of the CC0 legalcode along with
 *  this work.  If not, see
 *  <http://creativecommons.org/publicdomain/zero/1.0/>.
 **/
 #include <iostream>       // std::cout
 #include <string>         // std::string
 #include <cstddef>         // std::size_t
#include <modules/crystalvisualization/processors/coordinatereader.h>
#include <modules/hdf5/datastructures/hdf5handle.h>
#include <modules/hdf5/datastructures/hdf5path.h>

namespace inviwo {

// The Class Identifier has to be globally unique. Use a reverse DNS naming scheme
const ProcessorInfo CoordinateReader::processorInfo_{
    "envision.CoordinateReader",      // Class identifier
    "Coordinate Reader",                // Display name
    "Crystal",                          // Category
    CodeState::Experimental,  // Code state
    Tags::None,               // Tags
};
const ProcessorInfo CoordinateReader::getProcessorInfo() const {
    return processorInfo_;
}

CoordinateReader::CoordinateReader()
    : Processor()
    , outport_("outport")
    , inport_("inport")

    // New property for animations
    , timestep_("timestep", "Time step", false)
    , path_("path", "Path", "", InvalidationLevel::InvalidOutput, PropertySemantics::Default) {

    addPort(outport_);
    addPort(inport_);

    // New property for animations
    addProperty(timestep_);
    addProperty(path_);
}

void CoordinateReader::process() {


//Replacement string for path
auto path = path_.get();

//Find last '/' of path_ to be able to insert numbers
  int posStart = path.find_last_of('/') - 4;

//Function for counting how many digits
  int timestepINT = timestep_.get();
  int temp = timestep_.get();
  int count = 0;
    while (temp >= 1)
    {
        temp = temp / 10;
        ++count;
    }

 //If only one digit
  if (count == 1)
  {
    path.replace(posStart, 4, ("000" +  std::to_string(timestepINT)));
  }
  //If two digits
  if (count == 2)
  {
   path.replace(posStart, 4, ("00" +  std::to_string(timestepINT)));
  }
  //If three digits
  if (count == 3)
  {
   path.replace(posStart, 4, ("0" +  std::to_string(timestepINT)));
  }
  //If four digits
  if (count == 4)
  {
   path.replace(posStart, 4,  std::to_string(timestepINT));
  }

  path_.set(path);

  const auto h5path = hdf5::Path(path_.get());
  const auto data = inport_.getData();



    auto vecptr = std::make_shared<std::vector<vec3>>(data->getVectorOfVec3AtPath<float>(h5path));
    outport_.setData(vecptr);
}

} // namespace
