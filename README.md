# sat_hub_lib

`sat_hub_lib` is a Python package for downloading and extracting data from various satellite sources. It provides tools to work with GeoTIFF files, interact with S3 buckets, and process satellite imagery from Sentinel and other sources.

## Features

- Download and process satellite imagery from Sentinel Hub.
- Extract and manipulate GeoTIFF files.
- Cache management for S3 data.
- Support for various satellite data products including NDVI, RGB, and Landcover.

## Installation

To install the package, use:

```bash
git clone https://github.com/cl3t4p/sat_hub_lib.git
cd sat_hub_lib
python setup.py build
pip install .
```

## Requirements

- Python 3.7+
- boto3==1.36.3
- numpy==1.26.4
- rasterio==1.4.3
- shapely==2.0.6
- scipy==1.15.1
- pillow==11.1.0
- sentinelhub==3.11.0
- sympy==1.13.3

## Usage

### Basic Usage

```python
from sat_hub_lib import SentinelBaseSettings, RGB

# Define settings for Sentinel data
settings = SentinelBaseSettings(
    point1=(45.0, -93.0),
    point2=(46.0, -92.0),
    client_id='your_client_id',
    client_secret='your_client_secret',
    start_date='2023-01-01',
    end_date='2023-01-31',
    cloud_coverage=20,
    resolution=10
)

# Initialize the RGB product
rgb_product = RGB(conf=settings)

# Write the GeoTIFF file
rgb_product.write_geotiff(output_file='output/rgb_image.tif')

```

### Extracting Band Matrix

```python
from sat_hub_lib import S3_EsaWorldCover

# Initialize the S3_EsaWorldCover class
s3_esa = S3_EsaWorldCover(    
    point1=(45.45, 10.0),
    point2=(46.77, 10.98),
    version=2,
    disable_cache=True)


# Extract the matrix in bands so a 3d matrix with the first dimension being the band 
# S3_EsaWorldCover.extract_bandmatrix() has only 1 band
print(s3_esa.extract_bandmatrix())

```

### Using GProx
```python
from sat_hub_lib import GProx, S3_EsaWorldCover

# Initialize the S3_EsaWorldCover class
s3_esa = S3_EsaWorldCover(    
    point1=(45.45, 10.0),
    point2=(46.77, 10.98),
    version=2,
    disable_cache=True)

# Initialize the GProx class
gprox = GProx(s3_esa,20)
print(gprox.extract_bandmatrix()[0])

```
## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## Author

cl3t4p

## Acknowledgements

- [Sentinel Hub](https://www.sentinel-hub.com/)
- [Shapely](https://shapely.readthedocs.io/)
- [Rasterio](https://rasterio.readthedocs.io/)
- [SciPy](https://www.scipy.org/)
- [SymPy](https://www.sympy.org/)
- [Pillow](https://python-pillow.org/)
- [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
