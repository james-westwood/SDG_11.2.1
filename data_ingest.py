# Core imports for this module
import os

# Third party imports for this module
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
from zipfile import ZipFile
from io import BytesIO
import pyarrow.feather as feather


class Data_obj():
    # Class variables

    def __init__(self):
        self.crs = 'EPSG:27700'
        self.cwd = os.getcwd()
        self.data_dir = os.path.join(self.cwd,'data')
        self.zip_name = "Napatan.zip"
        self.zip_link = "http://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx?format=csv"
        self.feath_nm = "test.feather"
        self.feather_path = os.path.join(self.data_dir, self.feath_nm)
    
    def persistent_exists(self):
        """Checks if a persistent file already exists or not"""
        if os.path.isfile(self.feather_path):
            print(f"{self.feath_nm} already exists")
            return True
        else:
            print(f"{self.feath_nm} does not exist")
            return False 

    def dl_zip(self):
        """
        Downloads the zip file (which contains quite a few un-needed datasets) and holds it as 
            a zip-file in memory."""
        zip_path = os.path.join(self.data_dir, self.zip_name)
        # Grab the naptan zipfile from gov.uk
        print(f"Dowloading file from {self.zip_link}")
        filebytes = BytesIO(requests.get(self.zip_link).content)
        self.zip = ZipFile(filebytes)

    def zip_extract_csv(self):
        """
        Extracts csv from the zipfile held in memory 
        """
        CSV_NM = 'Stops.csv'
        with self.zip as the_zip:
            print(f"Extracting {CSV_NM} to {self.data_dir}")
            self.csv = the_zip.extract(CSV_NM, path=None)

    def csv_to_pd_df(self, delim, cols):
        """Function to create a Pandas dataframe from a csv file.

            Arguments:
                delim (string): the seperator in the csv file e.g. "," or "\t"
        """
        print("Converting csv data to Pandas DataFrame")
        self.pd_df = pd.read_csv(self.csv,
                        delim,
                        engine="python",
                        error_bad_lines=False,
                        quotechar='"',
                        usecols=cols)

    def pd_to_feather(self):
        """
        Writes a Pandas dataframe to feather for quick reading and retrieval later.
        """
        print(f"Writing Pandas dataframe to feather at {self.feather_path}")
        feather.write_feather(self.pd_df, self.feather_path)

    def feather_to_pd_df(self):
        self.pd_df = pd.read_feather(self.feather_path)



    def pd_df_to_gpd(self, geom_x, geom_y):
        """Makes a geo dataframe from Pandas dataframe.
            self.crs (string): the coordinate reference system required

            Arguments:
                geom_x (string):name of the column that contains the longitude data
                geom_y (string):name of the column that contains the latitude data
                
            Returns:
                Geopandas Dataframe"""
        geometry = [Point(xy) for xy in zip(self.pd_df[geom_x], self.pd_df[geom_y])]
        print("Converting Pandas DataFrame to GeoPandas DataFrame")
        geo_df = gpd.GeoDataFrame(self.pd_df, geometry=geometry)
        # Ensuring the CRS is in the geo df is correct 
        geo_df.crs = self.crs
        self.gpdf = geo_df.to_crs(self.crs)
    
data = Data_obj()
if data.persistent_exists():
    data.feather_to_pd_df()
else:
    data.dl_zip()
    data.zip_extract_csv()
    cols = ['NaptanCode', 'CommonName', 'Easting', 'Northing']
    data.csv_to_pd_df(delim=',', cols=cols)
    data.pd_to_feather()
geom_x='Easting'
geom_y='Northing'
data.pd_df_to_gpd(geom_x, geom_y)
print(data.gpdf)





    # def get_geo_dataset(url, localpath, filename):
    #     """Fetches a geodataset in json format from a web resource and
    #         saves it to the local data/ directory and returns the json
    #         as a dict into memory

    #     Args:
    #         filename (string): the name of file as it should be saved locally
    #         url (string): URL of the web resource where json file is hosted
    #         localpath (string): path to folder where json is to be saved locally
    #     Returns:
    #         json data as dict"""
    #     file = requests.get(url).json()
    #     full_path = os.path.join(localpath, filename)
    #     with open(full_path, 'w') as dset:
    #         json.dump(file, dset)
    #     return file







#     def json_to_pd_df(self):
#         pass



#     def shp_to_gpd_df(self):
#         pass









def geo_df_from_geospatialfile(path_to_file, crs='epsg:27700'):
    """Function to create a Geo-dataframe from a geospatial
        (geojson, shp) file. The process goes via Pandas.s

        Arguments:
            path_to_file (string): path to the geojson, shp and other
                geospatial data files

        Returns:
            Geopandas Dataframe
            """
    geo_df = gpd.read_file(path_to_file)
    if geo_df.crs != crs:
        geo_df = geo_df.to_crs('epsg:27700')
    return geo_df
