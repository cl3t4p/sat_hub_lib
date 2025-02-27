from abc import ABC, abstractmethod
import datetime
import os
from shapely import Polygon
from shapely.geometry import Point
import logging
import rasterio


class BaseProduct(ABC):
    

    # def __init__(self, config: dict):
    #     self.__output_file_path = self._gen_output_filepath(config["output"])
    #     #self.output_file = None
    #     self.log = logging.getLogger(type(self).__name__)
        
    def __init__(self,ouput_file: str = None):
        self.__output_file_path = self._gen_output_filepath(ouput_file)
        self.log = logging.getLogger(type(self).__name__)

    @abstractmethod
    def write_geotiff(self, output_file: str = None):
        """
        Abstract method to write the data to a GeoTIFF file.

        Parameters:
        output_file (str, optional): The path to the output GeoTIFF file. If not provided, a default path will used.

        Raises:
        NotImplementedError: This method must be overridden in a subclass.
        """


    @abstractmethod
    def extract_bandmatrix(self):
        """
        Abstract method to extract the band matrix from the data.

        Returns:
        np.ndarray: The band matrix. (Remember that the matrix is with the format [bands, rows, cols])

        Raises:
        NotImplementedError: This method must be overridden in a subclass.
        """
        pass

    def _gen_output_filepath(self, out_filepath):
        """
        Generates an output file path based on the provided template or class name.

        Args:
            outfolder (str): The template for the output file path. If it contains
                             the placeholder "*date_time*", it will be replaced with
                             the current date and time in the format "YYYY-MM-DD_HH-MM-SS".
                             If None, the output file path will be generated using
                             the class name and the current date and time.

        Returns:
            str: The generated output file path.
        """
        time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if out_filepath is not None:
            return out_filepath.replace("*date_time*", time)
        else:
            className = type(self).__name__
            # Default to use output folder
            return f"output/{className}_{time}.tif"

    def get_output_file_path(self, no_create=True) -> str:
        """
        Returns the output file path and creates the output folder if it does not exist.
        """
        if not os.path.exists(self.__output_file_path) and no_create:
            os.makedirs(os.path.dirname(self.__output_file_path), exist_ok=True)
        return self.__output_file_path
    
    def _default_rasterio_preprocess(self, geotiff):
        self.geotiff_meta = geotiff.meta
        self.geotiff_trasform = geotiff.transform

        data = geotiff.read()
        out_meta = geotiff.meta.copy()
        out_meta.update(
            height=data.shape[1],
            width=data.shape[2],
            driver="GTiff",
            count=data.shape[0],
            dtype=rasterio.uint8,
        )
        return data, out_meta


class BaseSatType(BaseProduct):

    # def __init__(self, config: dict):
    #     super().__init__(config)
    #     self.NW_point = Point(config["point1"])
    #     self.SE_point = Point(config["point2"])
    #     self.NW_Long = config["point1"][1]
    #     self.NW_Lat = config["point1"][0]
    #     self.SE_Long = config["point2"][1]
    #     self.SE_Lat = config["point2"][0]
    #     # Output folder

    #     self.bounding_box = Polygon(
    #         [
    #             (self.NW_Long, self.NW_Lat),
    #             (self.NW_Long, self.SE_Lat),
    #             (self.SE_Long, self.SE_Lat),
    #             (self.SE_Long, self.NW_Lat),
    #         ]
    #     )
    #     self.geotiff_trasform = None
    #     self.geotiff_meta = None

    def __init__(self,point1: tuple,point2: tuple,ouput_file: str = None):
        super().__init__(ouput_file)
        self.NW_point = Point(point1)
        self.SE_point = Point(point2)
        self.NW_Long = point1[1]
        self.NW_Lat = point1[0]
        self.SE_Long = point2[1]
        self.SE_Lat = point2[0]
        # Output folder

        self.bounding_box = Polygon(
            [
                (self.NW_Long, self.NW_Lat),
                (self.NW_Long, self.SE_Lat),
                (self.SE_Long, self.SE_Lat),
                (self.SE_Long, self.NW_Lat),
            ]
        )
        self.geotiff_trasform = None
        self.geotiff_meta = None