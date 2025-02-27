from sat_hub_lib.sentinel import SentinelBaseType
import sat_hub_lib.utils.geotiff_lib as geotiff_lib
from sentinelhub import SentinelHubRequest, DataCollection


class NDVI(SentinelBaseType):

    def write_geotiff(self, output_file: str = None):
        if output_file is None:
            output_file = self.get_output_file_path()
        super().write_geotiff(output_file)
        # Apply the color map
        geotiff_lib.apply_colormap(output_file, self.get_color_map())

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
/// Normalizes NDVI from [-0.5, 1] to [0, 150]
function setup() {
    return {
        input: ["B08", "B04"],
        output: { bands: 1, sampleType: "UINT8" }
    };
}

function evaluatePixel(sample) {
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    
    // Normalize NDVI from [-0.5, 1] to [0, 150]
    let normalized_ndvi = Math.round(((ndvi + 0.5) / 1.5) * 150);

    return [normalized_ndvi];
}
"""

    color_ramp = [
        (0, 0x0C0C0C),
        (30, 0xBFBFBF),
        (40, 0xDBDBDB),
        (50, 0xEAEAEA),
        (53, 0xFFF9CC),
        (55, 0xEDE8B5),
        (58, 0xDDD89B),
        (60, 0xCCC682),
        (63, 0xBCB76B),
        (65, 0xAFC160),
        (68, 0xA3CC59),
        (70, 0x91BF51),
        (75, 0x7FB247),
        (80, 0x70A33F),
        (85, 0x609635),
        (90, 0x4F892D),
        (95, 0x3F7C23),
        (100, 0x306D1C),
        (105, 0x216011),
        (110, 0x0F540A),
        (150, 0x004400),
    ]

    def get_color_map(self):
        return geotiff_lib.generate_colormap(self.color_ramp)
