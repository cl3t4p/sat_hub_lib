




from sat_hub_lib import GProx, S3_EsaWorldCover
import logging

logging.basicConfig(level=logging.INFO)

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