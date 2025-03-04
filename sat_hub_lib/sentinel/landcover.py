from enum import Enum
from .basetype_sent import SentinelBaseType, SentinelBaseSettings
from sentinelhub import SentinelHubRequest, DataCollection
import sat_hub_lib.utils.geotiff_lib as geotiff_lib
from sat_hub_lib.extension import IsMappable


class SAT_LANDCOVER_MAPCODE(Enum):
    BUILDINGS = 0, (255, 0, 0, 255)
    WATER = 1, (0, 0, 255, 255)
    TREES = 2, (0, 100, 0, 255)
    GRASS = 3, (154, 205, 50, 255)
    AGRICULTURE = 4, (255, 215, 0, 255)
    MOUNTAINS = 5, (139, 69, 19, 255)
    OTHER = 6, (210, 180, 140, 255)

    def __init__(self, code, color):
        self.code = code
        self.color = color

    @staticmethod
    def get_color_map():
        color_map = {}
        for item in SAT_LANDCOVER_MAPCODE:
            color_map[item.code] = item.color
        return color_map

    @staticmethod
    def get_color(code):
        for item in SAT_LANDCOVER_MAPCODE:
            if item.code == code:
                return item.color
        return (0, 0, 0, 255)


class Landcover(SentinelBaseType, IsMappable):
  
    def __init__(self, conf: SentinelBaseSettings,ndwi_threshold=0.2,ndvi_grass_min=0.3,ndvi_trees_min=0.6,ndbi_building_min=0.16):
      super().__init__(conf)
      self.ndwi_threshold = ndwi_threshold
      self.ndvi_grass_min = ndvi_grass_min
      self.ndvi_trees_min = ndvi_trees_min
      self.ndbi_building_min = ndbi_building_min
      

    def get_default_value_map(self):
        # Default value for mapping
        return {
            SAT_LANDCOVER_MAPCODE.TREES.code: 1,
            SAT_LANDCOVER_MAPCODE.GRASS.code: 0.8,
        }

    def write_geotiff(self, output_file: str = None):
        if output_file is None:
            output_file = self.get_output_file_path()
        super().write_geotiff(output_file)
        # Apply the color map
        geotiff_lib.apply_colormap(output_file, SAT_LANDCOVER_MAPCODE.get_color_map())

    def extract_bandmatrix(self):
        return super().extract_bandmatrix()

    def _get_input_type(self):
        return [
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(self.timeIntervalStart, self.timeIntervalEnd),
                other_args={"dataFilter": {"maxCloudCoverage": self.cloud_coverage}},
            ),
        ]

    def _get_evalscript(self) -> str:
        return """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B03", "B04", "B08", "B11",],
    }],
    output: { bands: 1, sampleType: "UINT8" }
  };
}

function evaluatePixel(samples) {
  let B04 = samples.B04; // Red
  let B03 = samples.B03; // Green
  let B08 = samples.B08; // NIR
  let B11 = samples.B11; // SWIR

  // Compute indices
  let ndvi = (B08 - B04) / (B08 + B04 + 0.00001);
  let ndwi = (B03 - B08) / (B03 + B08 + 0.00001);
  let ndbi = (B11 - B08) / (B11 + B08 + 0.00001);

  // Define thresholds (tune these for your location!)
  let waterThresh = WATER_PLACEHOLDER;
  let ndviGrassMin = GRASS_PLACEHOLDER;
  let ndviTreesMin = TREES_PLACEHOLDER;
  let ndbiBuildingMin = BUILDING_PLACEHOLDER;

  // 1. WATER
  if (ndwi > waterThresh) {
    return [1];
  }

  // 2. VEGETATION
  // If NDVI is above 0.3, we consider vegetation
  if (ndvi > ndviGrassMin) {
    if (ndvi > ndviTreesMin) {
      // Trees
      return [2];
    } else {
      // Grass
      return [3];
    }
  }
  
  // 3. BUILDINGS
  if (ndvi < ndviGrassMin && ndbi > ndbiBuildingMin) {
    return [0];
  }
  

  // 4. OTHER
  return [6];
}

""".replace("WATER_PLACEHOLDER", str(self.ndwi_threshold)) \
    .replace("GRASS_PLACEHOLDER", str(self.ndvi_grass_min)) \
    .replace("TREES_PLACEHOLDER", str(self.ndvi_trees_min)) \
    .replace("BUILDING_PLACEHOLDER", str(self.ndbi_building_min))
