# Core imports for this module
import os

# Third party imports for this module
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
from zipfile import ZipFile
from io import BytesIO


class Data_obj():
    # Class variables
    CWD = os.getcwd()

    def __init__(self):
        self.crs = 'EPSG:27700'
        self.cwd = os.getcwd()
        self.data_dir = os.path.join(self.cwd,'data')
        self.zip_name = "Napatan.zip"
        self.zip_link = "http://naptan.app.dft.gov.uk/DataRequest/Naptan.ashx?format=csv"
    
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


            
        
        # csv_path = os.path.join(self.data_dir, csv_nm)
        # # Open the zip file and extract
        
        # ZipFile.extract(csv_nm, path=self.data_dir)

    

data = Data_obj()
data.dl_zip()
print(type(data))
data.zip_extract_csv()
print(data.csv)



#     def check_file_exists(self, file_path):
#         """Checks if a persistent file already exists or not
#         """
#         # filenm = someregex
#         if os.path.isfile(file_path):
#             print(f"{filenm} already exists")
#             return True
#         else:
#             print(f"{filenm} does not exist")
#             return False 



#     def feather_to_pd_df(self):
#         pass



#     def csv_to_pd_df(self):
#         """Function to create a Geo-dataframe from a csv file.
#             The process goes via Pandas

#             Arguments:
#                 path_to_csv (string): path to the txt/csv containing geo data
#                     to be read
#                 delimiter (string): the seperator in the csv file e.g. "," or "\t"
#                 geom_x (string):name of the column that contains the longitude data
#                 geom_y (string):name of the column that contains the latitude data
#                 crs (string): the coordinate reference system required
#             Returns:
#                 Geopandas Dataframe
#         """
#         self.pd_df = pd.read_csv(path_to_csv,
#                         delim,
#                         engine="python",
#                         error_bad_lines=False,
#                         quotechar='"',
#                         usecols=cols)
#         return self.pd_df

#     def json_to_pd_df(self):
#         pass

#     def pd_df_to_gpd(self):
#         pass

#     def shp_to_gpd_df(self):
#         pass

#     def data_to_feather(self):
#         pass

# def dl_csv_make_df(csv_nm, csv_path, zip_name, zip_path, data_dir):
#     """
    
#     Checks if the csv is already download/extracted so it doesn't have to
#     go through the process again.
#     """
#     # Check if csv exists


            
        

#     return True

# def geo_df_from_csv(path_to_csv, geom_x, geom_y, cols, crs, delim=','):

    
#     geometry = [Point(xy) for xy in zip(pd_df[geom_x], pd_df[geom_y])]
#     geo_df = gpd.GeoDataFrame(pd_df, geometry=geometry)
#     geo_df.crs = crs
#     geo_df.to_crs(crs, inplace=True)
#     return geo_df


# # def get_and_save_geo_dataset(url, localpath, filename):
# #     """Fetches a geodataset in json format from a web resource and
# #         saves it to the local data/ directory and returns the json
# #         as a dict into memory

# #     Args:
# #         filename (string): the name of file as it should be saved locally
# #         url (string): URL of the web resource where json file is hosted
# #         localpath (string): path to folder where json is to be saved locally
# #     Returns:
# #         json data as dict"""
# #     file = requests.get(url).json()
# #     full_path = os.path.join(localpath, filename)
# #     with open(full_path, 'w') as dset:
# #         json.dump(file, dset)
# #     return file


# def geo_df_from_geospatialfile(path_to_file, crs='epsg:27700'):
#     """Function to create a Geo-dataframe from a geospatial
#         (geojson, shp) file. The process goes via Pandas.s

#         Arguments:
#             path_to_file (string): path to the geojson, shp and other
#                 geospatial data files

#         Returns:
#             Geopandas Dataframe
#             """
#     geo_df = gpd.read_file(path_to_file)
#     if geo_df.crs != crs:
#         geo_df = geo_df.to_crs('epsg:27700')
#     return geo_df
