#include <modules/graph2d/processors/plot2d.h>

#include <modules/plotting/utils/axisutils.h>
#include <modules/opengl/texture/textureutils.h>
#include <inviwo/core/util/raiiutils.h>
#include <inviwo/core/algorithm/boundingbox.h>
#include <inviwo/core/rendering/meshdrawerfactory.h>


#include <modules/opengl/texture/textureutils.h>
#include <modules/opengl/shader/shaderutils.h>
#include <modules/opengl/openglutils.h>


#include <modules/opengl/openglutils.h>
#include <inviwo/core/datastructures/coordinatetransformer.h>
#include <modules/opengl/texture/textureutils.h>

namespace inviwo {


// The Class Identifier has to be globally unique. Use a reverse DNS naming scheme
const ProcessorInfo Plot2dProcessor::processorInfo_{
    "org.inviwo.Plot2D",    // Class identifier
    "Plot2D",                 // Display name
    "Plotting",               // Category
    CodeState::Stable,        // Code state
    "Plotting",           // Tags
};

const ProcessorInfo Plot2dProcessor::getProcessorInfo() const { return processorInfo_; }

Plot2dProcessor::Plot2dProcessor()
    : Processor()
    , inport_("inport")
    , imageInport_("imageInport")
	, meshOutport_("meshOutport")
    , outport_("outport")
    , xAxis_("xAxis", "X Axis")
    , yAxis_("yAxis", "Y Axis")
	, position_("position", "Position", vec3(0), vec3(-25), vec3(25), vec3(0.01))
	, size_("size", "Size", vec2(3), vec2(0.01), vec2(25), vec2(0.01))
    , camera_("camera", "Camera")
	, camera2d_{ InviwoApplication::getPtr()->getCameraFactory()->create("OrthographicCamera") }
    , trackball_(&camera_)
	, axisRenderers_({ {xAxis_, yAxis_} })
	, xAxisSelection_("xAxisSelection", "X Axis")
	, yAxisSelection_("yAxisSelection", "Y Axis")
	, toggle3d_("toggle3d", "Render in 3D space")
	, lineMesh_( std::make_shared<BasicMesh>() )
	, meshDrawer_( std::unique_ptr<MeshDrawer>() )
	//, shader_("meshrendering.vert", "meshrendering.frag", false)
	, shader_("linerenderer.vert", "linerenderer.geom", "linerenderer.frag", false)
	, lightingProperty_("lighting", "Lighting", &camera_)
    {

	shader_.onReload([this]() { invalidate(InvalidationLevel::InvalidResources); });
	

	MeshDrawerFactory* factory = InviwoApplication::getPtr()->getMeshDrawerFactory();
	meshDrawer_ = std::move(factory->create(lineMesh_.get()));

	// Initialize the 2d camera.
	camera2d_->setLookFrom(vec3(0, 0, 100));
	camera2d_->setLookTo(vec3(0, 0, 0));
	camera2d_->setLookUp(vec3(0, 1, 0));
	camera2d_->setFarPlaneDist(200);
	camera2d_->setNearPlaneDist(1);

	// Setup ports
    imageInport_.setOptional(true);
    addPort(inport_);
    addPort(imageInport_);
    addPort(outport_);
	addPort(meshOutport_);

	// Add properties
	addProperty(toggle3d_);
	addProperty(position_);
	addProperty(size_);
	addProperties(xAxisSelection_, yAxisSelection_);
	addProperties(xAxis_, yAxis_);
	addProperty(camera_);
	addProperty(trackball_);
	addProperty(lightingProperty_);

	// Setup property default values
	xAxis_.setCaption("x");
	yAxis_.setCaption("y");
	yAxis_.orientation_.setSelectedDisplayName("Vertical");
	xAxis_.setCollapsed(true);
	yAxis_.setCollapsed(true);

	toggle3d_.set(false);
	camera_.setVisible(false);
	trackball_.setVisible(false);

	camera_.setVisible(false);
	trackball_.setVisible(false);
	camera_.setCollapsed(true);
	trackball_.setCollapsed(true);

	// Event callbacks
	toggle3d_.onChange([this] {
		position_.setVisible(toggle3d_.get());
		size_.setVisible(toggle3d_.get());
		camera_.setVisible(toggle3d_.get());
		trackball_.setVisible(toggle3d_.get());
		updateDimensions();
	});
	size_.onChange([this] { updateDimensions(); });
	position_.onChange([this] { updateDimensions(); });

	inport_.onChange([this] { 
		reloadDatasets();
		updatePlotData(); });
	xAxisSelection_.onChange([this] { updatePlotData(); });
	yAxisSelection_.onChange([this] { updatePlotData(); });
	xAxis_.range_.onChange([this] { updatePlotData(); });
	yAxis_.range_.onChange([this] { updatePlotData(); });
	xAxis_.useDataRange_.onChange([this] { updatePlotData(); });
	yAxis_.useDataRange_.onChange([this] { updatePlotData(); });
	
	// Initialize axis default values.
	for (auto axis : { &xAxis_, &yAxis_ }) {
		axis->captionSettings_.offset_.set(0.7f);
		axis->captionSettings_.position_.set(0.5f);
		axis->labelSettings_.offset_.set(0.7f);

		axis->majorTicks_.tickLength_.set(0.3f);
		axis->majorTicks_.tickWidth_.set(1.5f);
		axis->majorTicks_.style_.set(plot::TickStyle::Outside);
		axis->majorTicks_.setCurrentStateAsDefault();

		axis->minorTicks_.tickLength_.set(0.15f);
		axis->minorTicks_.tickWidth_.set(1.3f);
		axis->minorTicks_.style_.set(plot::TickStyle::Outside);
		axis->minorTicks_.setCurrentStateAsDefault();
	}
}


void Plot2dProcessor::initializeResources() {
	LogInfo("Initializing resources plot2d");

	shader_[ShaderType::Geometry]->addShaderDefine("ENABLE_ADJACENCY", "1");
	//shader_[ShaderType::Fragment]->addShaderDefine("ENABLE_ROUND_DEPTH_PROFILE");

	// See createLineStripMesh()
	shader_[ShaderType::Vertex]->addInDeclaration("in_" + toString(BufferType::PositionAttrib),
		static_cast<int>(BufferType::PositionAttrib),
		"vec3");
	shader_[ShaderType::Vertex]->addInDeclaration("in_" + toString(BufferType::ColorAttrib),
		static_cast<int>(BufferType::ColorAttrib),
		"vec4");
	shader_[ShaderType::Vertex]->addInDeclaration("in_" + toString(BufferType::TexcoordAttrib),
		static_cast<int>(BufferType::TexcoordAttrib),
		"vec2");
	shader_.build();
	shader_.activate();
	shader_.setUniform("antialiasing", 0.8f);
	shader_.setUniform("miterLimit", 1.0f);
	shader_.deactivate();
}


void Plot2dProcessor::process() {
	LogInfo("Process start");
	if (imageInport_.isReady()) {
		utilgl::activateTargetAndCopySource(outport_, imageInport_, ImageType::ColorDepth);
	}
	else {
		utilgl::activateAndClearTarget(outport_, ImageType::ColorDepth);
	}
	const size2_t dims = outport_.getDimensions();
	if (!toggle3d_.get() && oldDims_ != dims) updateDimensions();
	
	// Save a pointer to the camera that will be used
	Camera* activeCamera;
	if (toggle3d_.get())
		activeCamera = &camera_.get();
	else
		activeCamera = camera2d_.get();

	vec3 xDir(1, 0, 0);
	vec3 yDir(0, 1, 0);

	if (toggle3d_.get()) {
		// Direct the graph to face the camera.
		yDir = glm::normalize( camera_.getLookUp() );
		xDir = glm::normalize( glm::cross(yDir, camera_.getLookFrom() - camera_.getLookTo()) );

		lineMesh_->setBasis(Matrix<3U, float>(
			graphDims_[0] * xDir.x, graphDims_[0] * xDir.y, graphDims_[0] * xDir.z,
			graphDims_[1] * yDir.x, graphDims_[1] * yDir.y, graphDims_[1] * yDir.z,
			0, 0, 1));
	}

	// Render x and y axis

	axisRenderers_[0].render(activeCamera, dims, origin_, origin_ + xDir * graphDims_[0], yDir);
	axisRenderers_[1].render(activeCamera, dims, origin_, origin_ + yDir * graphDims_[1], xDir);

	//axisRenderers_[0].render(activeCamera, dims, origin_, origin_ + xDir*graphDims_[0], vec3(0.0f, 1.0f, 0.0f));
	//axisRenderers_[1].render(activeCamera, dims, origin_, origin_ + yDir*graphDims_[1], vec3(1.0f, 0.0f, 0.0f));
	
	// Render lines.
	shader_.activate();
	//utilgl::setUniforms(shader_, lightingProperty_);
	
	
	utilgl::setShaderUniforms(shader_, *meshDrawer_->getMesh(), "geometry");
	utilgl::setShaderUniforms(shader_, *activeCamera, "camera");
	shader_.setUniform("screenDim", vec2(outport_.getDimensions()));
	//shader_.setUniform("camera", *activeCamera);
	shader_.setUniform("lineWidth", 2);



	meshDrawer_->draw();
	shader_.deactivate();

	utilgl::deactivateCurrentTarget();
}


void Plot2dProcessor::reloadDatasets() {
	if (!inport_.hasData()) {
		xAxisSelection_.clearOptions();
		yAxisSelection_.clearOptions();
		return;
	}
	const std::shared_ptr<const DataFrame> dataframe = inport_.getData();
	// Update column selection properties
	std::vector<OptionPropertyStringOption> options;
	for (const auto& column : *dataframe) {
		options.emplace_back(column->getHeader(), column->getHeader(), column->getHeader());
	}

	xAxisSelection_.replaceOptions(options);
	yAxisSelection_.replaceOptions(options);
	xAxisSelection_.setCurrentStateAsDefault();
	yAxisSelection_.setCurrentStateAsDefault();
}

void Plot2dProcessor::updateDimensions() {
	if (toggle3d_.get()) {
		origin_ = position_.get();
		graphDims_ = size_.get();
	}
	else {
		const size2_t dims = outport_.getDimensions();
		const float aspect = (float)dims[0] / (float)dims[1];
		const float scale = (double)dims[0] / 512;
		const float width = 50 * scale;
		const float height = width / aspect;
		const float padding = 50 * width / (double)dims[0];

		oldDims_ = dims;
		origin_ = vec3(-width / 2 + padding, -height / 2 + padding, 0);
		graphDims_ = vec2(width - 2 * padding, height - 2 * padding);
		// Update 2d camera to fit new dimensions.
		static_cast<OrthographicCamera*>(camera2d_.get())->setFrustum({ -width / 2.0f, +width / 2.0f, -width / 2.0f / aspect, +width / 2.0f / aspect });
	}
	// Scale and offset line mesh to align with axises.
	lineMesh_->setBasis(Matrix<3U, float>(graphDims_[0], 0, 0, 0, graphDims_[1], 0, 0, 0, 1));
	lineMesh_->setOffset(origin_);
}



void Plot2dProcessor::updatePlotData() {
	// Reset line mesh
	lineMesh_ = std::make_shared<BasicMesh>(); 
	meshDrawer_ = std::move(InviwoApplication::getPtr()->getMeshDrawerFactory()->create(lineMesh_.get()));


	if (!inport_.hasData()) return;

	const std::shared_ptr<const DataFrame> dataframe = inport_.getData();
	const std::shared_ptr<const Column> xCol = dataframe->getColumn(xAxisSelection_.getSelectedIndex());
	const std::shared_ptr<const Column> yCol = dataframe->getColumn(yAxisSelection_.getSelectedIndex());


	size_t nValues = xCol->getSize();

	if (xCol->getSize() < 2 || yCol->getSize() < 2 || yCol->getSize() != xCol->getSize()) return;
	
	


	// Sort by x axis?


	// Set ranges for x and y axis
	if (xAxis_.getUseDataRange()) {
		LogInfo("Autosetting x range");
		dvec2 xrange(xCol->getAsDouble(0), xCol->getAsDouble(0));
		for (size_t i = 1; i < nValues; ++i) {
			double v = xCol->getAsDouble(i);
			if (v < xrange[0]) xrange[0] = v;
			if (v > xrange[1]) xrange[1] = v;
		}
		xAxis_.range_.set(xrange);
	}

	if (yAxis_.getUseDataRange()) {
		LogInfo("Autosetting y range");
		dvec2 yrange(yCol->getAsDouble(0), yCol->getAsDouble(0));
		for (size_t i = 1; i < nValues; ++i) {
			if (xCol->getAsDouble(i) < xAxis_.getRange()[0] || xCol->getAsDouble(i) > xAxis_.getRange()[1]) {
				LogInfo("Bad X: " << xCol->getAsDouble(i));
				continue;
			}
			double v = yCol->getAsDouble(i);
			if (v < yrange[0]) yrange[0] = v;
			if (v > yrange[1]) yrange[1] = v;
		}
		if (yrange[0] == yrange[1]) yrange[1] += 1;
		yAxis_.range_.set(yrange);
	}

	const double offsetX = -xAxis_.getRange()[0];
	const double offsetY = -yAxis_.getRange()[0];
	const double scaleX = 1.0f / (xAxis_.getRange()[1] - xAxis_.getRange()[0]);
	const double scaleY = 1.0f / (yAxis_.getRange()[1] - yAxis_.getRange()[0]);

	//std::shared_ptr<IndexBufferRAM> indices = lineMesh_->addIndexBuffer(DrawType::Lines, ConnectivityType::None);
	std::shared_ptr<IndexBufferRAM> indices = lineMesh_->addIndexBuffer(DrawType::Lines, ConnectivityType::StripAdjacency);
	vec4 color(1, 0, 0, 1);
	const auto notInRange = [](const vec3& p) { 
		return p.x < 0 || p.x > 1 || p.y < 0 || p.y > 1;
	};

	auto getPoint = [xCol, yCol, offsetX, offsetY, scaleX, scaleY](const size_t index) {
		return vec3((xCol->getAsDouble(index) + offsetX)*scaleX, (yCol->getAsDouble(index) + offsetY)*scaleY, 0);
	};
	//// Add point from dataframe to line mesh
	for (size_t i = 0; i < nValues; ++i) {
		const vec3 p1((xCol->getAsDouble(i) + offsetX)*scaleX, (yCol->getAsDouble(i) + offsetY)*scaleY, 0);
		//const vec3 p2((xCol->getAsDouble(i+1) + offsetX)*scaleX, (yCol->getAsDouble(i+1) + offsetY)*scaleY, 0);
		if (notInRange(p1)) continue;
		indices->add(lineMesh_->addVertex(p1, p1, p1, color));
		//indices->add(lineMesh_->addVertex(p2, p2, p2, color));
	}
	

	// Update the dimensions of the mesh.
	updateDimensions();


}














} // namespace