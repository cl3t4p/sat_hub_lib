from sat_hub_lib.baseproducts import BaseSatType

class BaseSat_GeoTiff(BaseSatType):
    def __init__(self,point1: tuple, point2: tuple,output_filepath: str = None):
        super().__init__(point1,point2,output_filepath)