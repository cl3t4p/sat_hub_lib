from abc import ABC, abstractmethod
import datetime
import numpy as np
import rasterio
from scipy import signal
import sympy as sp
from sat_hub_lib.baseproducts import BaseSatType, BaseProduct


class IsMappable(ABC):

    @abstractmethod
    def get_default_value_map(self):
        raise NotImplementedError


class GProx(BaseProduct):

    # def __init__(self, product: BaseSatType, config):
    #     super().__init__(config)
    #     self.meter_radius = config["meter_radius"]
    #     self.value_map = config.get("value_map", None)
    #     self.product = product
    #     self.matrix = None

    #     if self.value_map is None:
    #         if self.product.get_default_value_map is not None:
    #             self.value_map = self.product.get_default_value_map()
    #         else:
    #             raise ValueError(f"Value map {self.product.__class__.__name__} is not provided and the product does not have a default value map.")

    def __init__(
        self,
        product: BaseSatType,
        meter_radius: int,
        value_map: dict = None,
        omega=1,
        function="1-(x/r)**o",
        output_filepath: str = None,
    ):
        """
        Initialize the Gprox class.
        Args:
            product (BaseSatType): The satellite product.
            meter_radius (int): The radius in meters.
            value_map (dict, optional): A dictionary mapping values. Defaults to None.
            omega (int, optional): The omega value for the function. Defaults to 1.
            function (str, optional): The function to be used. Defaults to '1-(x/r)**o'.
            output_filepath (str, optional): The file path for the output. Defaults to None.
        Raises:
            ValueError: If value_map is not provided and the product does not have a default value map.
        """
        self.product = product
        super().__init__(output_filepath)
        self.meter_radius = meter_radius
        self.value_map = value_map
        self.matrix = None
        self.omega = omega
        self.function = function

        if self.value_map is None:
            if self.product.get_default_value_map is not None:
                self.value_map = self.product.get_default_value_map()
            else:
                raise ValueError(
                    f"Value map {self.product.__class__.__name__} is not provided and the product does not have a default value map."
                )

    def write_geotiff(self, output_file: str = None):
        if output_file is None:
            output_file = self.get_output_file_path()

        matrix = self.extract_bandmatrix()
        with rasterio.open(output_file, "w", **self.product.geotiff_meta) as dst:
            dst.write(matrix.astype(rasterio.uint8), 1)
            dst.meta.update(
                {
                    "driver": "GTiff",
                    "height": matrix.shape[0],
                    "width": matrix.shape[1],
                    "transform": self.product.geotiff_trasform,
                    "count": 1,
                    "dtype": rasterio.uint8,
                }
            )
        # Create a green gradient colormap
        color_map = {i: (0, i, 0, 255) for i in range(256)}

        # Write the colormap
        with rasterio.open(output_file, "r+") as src:
            src.write_colormap(1, color_map)
        self.log.info("Matrix written to GeoTIFF at " + output_file)

    def extract_bandmatrix(self):
        """
        Extracts a percentage matrix based on the target values and a circular kernel.
        This method performs the following steps:
        1. Extracts the initial matrix from the product.
        2. Logs the start of the percentage matrix calculation.
        3. Creates a circular kernel based on the product's resolution type (either integer or tuple).
        4. Parses a function expression to generate the kernel values.
        5. Maps the target values to a matrix.
        6. Convolves the target matrix with the kernel using FFT to count target occurrences.
        7. Convolves a ones matrix with the kernel to count total valid cells per pixel neighborhood.
        8. Calculates the percentage matrix by dividing the target counts by the total valid cells.
        9. Logs the completion of the percentage matrix calculation and its shape.
        Returns:
            np.ndarray: The calculated percentage matrix.
        Raises:
            ValueError: If the product resolution type is unsupported.
        """

        # Get the matrix from the product
        matrix = self.product.extract_bandmatrix()[0]
        self.log.info("Starting percentage matrix calculation")

        # Create the kernel based on resolution type.
        if isinstance(self.product.resolution, int):

            # Create a circular kernel with increasing values outward (normalized to [0,1])
            radius = self.meter_radius / self.product.resolution
            y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
            distance = np.sqrt(x**2 + y**2)

            # Compute kernel values, ensuring they stay within [0,1] using formula: (r - d) / r
            # circular_kernel = np.clip((radius - distance) / radius, 0, 1)

        elif isinstance(self.product.resolution, tuple):
            # Unpack the resolution for width and height (e.g., (res_x, res_y) in meters per pixel or degrees converted via a factor)
            res_x, res_y = self.product.resolution
            # Calculate how many pixels in each direction correspond to the meter radius.
            radius_x = self.meter_radius / res_x
            radius_y = self.meter_radius / res_y
            # Create grid indices for y and x:
            y, x = np.ogrid[-radius_y : radius_y + 1, -radius_x : radius_x + 1]
            # Compute the physical distance for each cell:
            # Note: x and y here are in pixel offsets; multiply by the corresponding resolution.
            distance = np.sqrt((x * res_x) ** 2 + (y * res_y) ** 2)
            # Create the kernel: cells within the meter_radius get a value that linearly decays from 1 (at center) to 0 at the edge.
            # circular_kernel = np.clip((self.meter_radius - distance) / self.meter_radius, 0, 1)
        else:
            raise ValueError("Unsupported resolution type")

        kernel_function = self.parse_function_expression(self.function)
        circular_kernel = np.clip(
            kernel_function(distance, self.meter_radius, self.omega), 0, 1
        )

        # Get the target value map
        target_value = self.value_map

        if isinstance(target_value, dict):
            # Create a matrix with the target values mapped to integers.
            target_matrix = np.zeros_like(matrix, dtype=float)
            for value, target in target_value.items():
                target_matrix[matrix == value] = target
        elif isinstance(target_value, int):
            # Create a binary matrix: 1 where the matrix equals target_value, 0 otherwise.
            target_value = self.value_to_map
            target_matrix = (matrix == target_value).astype(float)

        # Convolve the target matrix with the kernel using FFT to count target occurrences.
        target_counts = signal.fftconvolve(target_matrix, circular_kernel, mode="same")

        # Convolve a ones matrix with the kernel to count total valid cells per pixel neighborhood.
        total_cells = signal.fftconvolve(
            np.ones_like(matrix, dtype=float), circular_kernel, mode="same"
        )

        # Calculate percentage (with safe division).
        percentageMatrix = (
            np.divide(
                target_counts,
                total_cells,
                out=np.zeros_like(target_counts),
                where=total_cells != 0,
            )
            * 100
        )
        self.log.info(
            f"Percentage matrix calculated with shape {percentageMatrix.shape}"
        )
        return percentageMatrix

    def parse_function_expression(self, expression: str):
        """
        Converts a user-provided string function into a callable function.
        Example: "1 - (x / r) ** o" will be converted to a function that calculates 1 - (x / r) ** o.
        """
        x, r, o = sp.symbols("x r o")  # Define symbolic variables
        expr = sp.sympify(expression)  # Convert string to sympy expression
        return sp.lambdify(
            (x, r, o), expr, "numpy"
        )  # Convert to a NumPy-compatible function

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
            className = type(self.product).__name__
            # Default to use output folder
            return f"output/GProx_{className}_{time}.tif"
