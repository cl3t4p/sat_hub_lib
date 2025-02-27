from abc import abstractmethod
from io import BytesIO
import rasterio
from sat_hub_lib.baseproducts import BaseSatType
from sentinelhub import SentinelHubRequest, MimeType, CRS, SHConfig
import sentinelhub
import sat_hub_lib.sentinel.sentinel_lib as sentinel_lib


class SentinelBaseSettings:
    def __init__(
        self,
        point1: tuple,
        point2: tuple,
        client_id: str,
        client_secret: str,
        start_date: str,
        end_date: str,
        cloud_coverage: float = 20,
        resolution: int = None,
        output_file: str = None,
    ):
        self.point1 = point1
        self.point2 = point2
        self.client_id = client_id
        self.client_secret = client_secret
        self.start_date = start_date
        self.end_date = end_date
        self.cloud_coverage = cloud_coverage
        self.resolution = resolution
        self.output_file = output_file


class SentinelBaseType(BaseSatType):

    max_resolution_allowed = 2500  # Sentinel Hub allows a maximum resolution of 2500 pixel for the width and height

    # def __init__(self, config: dict):
    #     # Initialize the base class with the configuration parameters
    #     super().__init__(config)

    #     # Auth configuration for Sentinel Hub
    #     self.config = SHConfig()
    #     self.config.sh_client_id = config["client_id"]
    #     self.config.sh_client_secret = config["client_secret"]

    #     # Time interval
    #     self.timeIntervalStart = config["start_date"]
    #     self.timeIntervalEnd = config["end_date"]

    #     # Geographical parameters
    #     self.cloud_coverage = config["cloud_coverage"]

    #     self.resolution = config.get("resolution",None)
    #     self.sat_hub_bounding_box = sentinelhub.BBox(
    #         bbox=self.bounding_box.bounds, crs=CRS.WGS84
    #     )

    #     #sentinelhub.bbox_to_dimensions(self.sat_hub_bounding_box, self.resolution)
    #     if self.resolution is None:
    #         self.resolution = 5
    #         self.resolution = sentinel_lib.get_valid_resolution(self.sat_hub_bounding_box, self.resolution)
    #     self.log.info(
    #         f"Resolution: {self.resolution}"
    #     )

    def __init__(self, conf: SentinelBaseSettings):

        super().__init__(conf.point1, conf.point2, conf.output_file)

        # Auth configuration for Sentinel Hub
        self.config = SHConfig()
        self.config.sh_client_id = conf.client_id
        self.config.sh_client_secret = conf.client_secret

        # Time interval
        self.timeIntervalStart = conf.start_date
        self.timeIntervalEnd = conf.end_date

        # Geographical parameters
        self.cloud_coverage = conf.cloud_coverage

        self.resolution = conf.resolution
        self.sat_hub_bounding_box = sentinelhub.BBox(
            bbox=self.bounding_box.bounds, crs=CRS.WGS84
        )

        # sentinelhub.bbox_to_dimensions(self.sat_hub_bounding_box, self.resolution)
        if self.resolution is None:
            self.resolution = 5
            self.resolution = sentinel_lib.get_valid_resolution(
                self.sat_hub_bounding_box, self.resolution
            )
        self.log.info(f"Resolution: {self.resolution}")

    def _get_response(self):
        self.log.info("Getting data from Sentinel Hub")
        request = self.get_request()
        response = request.get_data(
            save_data=False, show_progress=True, decode_data=False
        )
        return response

    def write_geotiff(self, output_file: str = None):
        if output_file is None:
            output_file = self.get_output_file_path()

        response = self._get_response()

        # self.output_file = output_file

        data_in_memory = BytesIO(response[0].content)
        with rasterio.open(data_in_memory) as src:
            data, meta = self._default_rasterio_preprocess(src)
            _range = data.shape[0]

            with rasterio.open(output_file, "w", **meta) as dst:
                for i in range(1, _range + 1):
                    dst.write(data[i - 1], i)

    def extract_bandmatrix(self):
        response = self._get_response()

        data_in_memory = BytesIO(response[0].content)
        with rasterio.open(data_in_memory) as src:
            data, meta = self._default_rasterio_preprocess(src)
            return data

    def get_request(self) -> SentinelHubRequest:
        converted_resolution = sentinel_lib.get_resolution_degree_from_meters(
            self.sat_hub_bounding_box, self.resolution
        )
        request = SentinelHubRequest(
            evalscript=self._get_evalscript(),
            data_folder=self.get_output_file_path(False),
            input_data=self._get_input_type(),
            responses=self._get_response_type(),
            resolution=converted_resolution,
            bbox=self.sat_hub_bounding_box,
            config=self.config,
        )
        return request

    def _get_response_type(self) -> list:
        return [
            SentinelHubRequest.output_response("default", MimeType.TIFF),
        ]

    @abstractmethod
    def _get_input_type(self) -> list:
        pass

    @abstractmethod
    def _get_evalscript(self) -> str:
        pass
