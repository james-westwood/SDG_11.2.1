# Core imports
import os

# Third party imports
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import yaml

# Module imports
from geospatial_mods import *
from data_ingest import *
from data_transform import *

# get current working directory
CWD = os.getcwd()
# TODO: find out best practice on CWD

# Load config
with open(os.path.join(CWD, "config.yaml")) as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    print("Config loaded")

# Constants
DEFAULT_CRS = config["DEFAULT_CRS"]
DATA_DIR = config["DATA_DIR"]
EXT_ORDER = config['EXT_ORDER']

# define url for zip download
NAPT_ZIP_LINK = config["NAPT_ZIP_LINK"]

# Define the columns wanted from Naptan
COLS = list(config["NAPTAN_TYPES"].keys())
NAPTAN_DTYPES = config["NAPTAN_TYPES"]
# Get the pandas dataframe for the stops data
stops_df = any_to_pd(file_nm="Stops", 
                     zip_link=NAPT_ZIP_LINK, 
                     ext_order=EXT_ORDER,
                     dtypes=NAPTAN_DTYPES)

stops_geo_df = (geo_df_from_pd_df(pd_df=stops_df,
                                geom_x='Easting',
                                geom_y='Northing',
                                crs=DEFAULT_CRS))

# # Getting the Lower Super Output Area for the UK into a dataframe
uk_LSOA_shp_file = "Lower_Layer_Super_Output_Areas__December_2011__Boundaries_EW_BGC.shp"
full_path = os.path.join(os.getcwd(), "data", "LSOA_shp", uk_LSOA_shp_file)
uk_LSOA_df = geo_df_from_geospatialfile(path_to_file=full_path)

# Get a polygon of Birmingham based on the Location Code
just_birmingham_poly = (get_polygons_of_loccode(
                        geo_df=uk_LSOA_df, 
                        dissolveby='LSOA11NM',
                        search="Birmingham"))

# Creating a Geo Dataframe of only stops in Birmingham

birmingham_stops_geo_df = (find_points_in_poly
                           (geo_df=stops_geo_df,
                            polygon_obj=just_birmingham_poly))

# Getting the west midlands population
Wmids_pop_df = pd.read_csv(os.path.join
                           (DATA_DIR,
                            'population_estimates',
                            'westmids_pop_only.csv'))

# Get population weighted centroids into a dataframe
uk_pop_wtd_centr_df = (geo_df_from_geospatialfile
                       (os.path.join
                        (DATA_DIR,
                         'pop_weighted_centroids')))

# Get output area boundaries
OA_df = pd.read_csv('https://opendata.arcgis.com/datasets/7763a773b61445128ed3251e27be5139_0.csv?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D')

# Merge with uk population df
uk_pop_wtd_centr_df = uk_pop_wtd_centr_df.merge(OA_df, on="OA11CD", how='left')

# Clean after merge
uk_pop_wtd_centr_df.drop('OBJECTID_y', axis=1, inplace=True)
uk_pop_wtd_centr_df.rename({'OBJECTID_x': 'OBJECTID'}, inplace=True)

# Getting the urban-rural classification by OA for England and Wales
Urb_Rur_ZIP_LINK = config["Urb_Rur_ZIP_LINK"]
URB_RUR_TYPES = config["URB_RUR_TYPES"]

# Make a df of the urban-rural classification
urb_rur_df = any_to_pd("RUC11_OA11_EW", Urb_Rur_ZIP_LINK, ['csv'], URB_RUR_TYPES)

# These are the codes (RUC11CD) mapping to rural and urban descriptions (RUC11)
# I could make this more succinct, but leaving here for clarity and maintainability
urban_dictionary = {'A1': 'Urban major conurbation', 
                    'C1': 'Urban city and town', 
                    'B1': 'Urban minor conurbation',
                    'C2': 'Urban city and town in a sparse setting'}
rural_dictionary = {'F1': 'Rural hamlets and isolated dwellings',
                    'E1': 'Rural village',
                    'D1': 'Rural town and fringe',
                    'E2': 'Rural village in a sparse setting',
                    'F2': 'Rural hamlets and isolated dwellings in a sparse setting',
                    'D2': 'Rural town and fringe in a sparse setting'}

# mapping to a simple urban or rural classification
urb_rur_df["urb_rur_class"] =  (urb_rur_df.RUC11CD.map
                                (lambda x: "urban" 
                                if x in urban_dictionary.keys() 
                                else "rural"))
# filter the df. We only want OA11CD and an urban/rurual classification
urb_rur_df = urb_rur_df[['OA11CD','urb_rur_class']]

# joining urban rural classification onto the pop df
uk_pop_wtd_centr_df = uk_pop_wtd_centr_df.merge(urb_rur_df, on="OA11CD", how='left')

# Joining the West Mids population dataframe to the centroids dataframe, #forthedemo
Wmids_pop_df = Wmids_pop_df.join(
    other=uk_pop_wtd_centr_df.set_index('OA11CD'), on='OA11CD', how='left')

# Make B'ham LSOA just #forthedemo
bham_LSOA_df = uk_LSOA_df[uk_LSOA_df.LSOA11NM.str.contains("Birmingham")] 
bham_LSOA_df = bham_LSOA_df[['LSOA11CD', 'LSOA11NM', 'geometry']]

# merge the two dataframes limiting to just Birmingham #forthedemo
bham_pop_df = Wmids_pop_df.merge(bham_LSOA_df,
                                 how='right',
                                 left_on='LSOA11CD',
                                 right_on='LSOA11CD',
                                 suffixes=('_pop', '_LSOA'))
# rename the "All Ages" column to pop_count as it's the population count 
bham_pop_df.rename(columns={"All Ages": "pop_count"}, inplace=True)

# change pop_count to number (int)
bham_pop_df['pop_count'] = pd.to_numeric(bham_pop_df.pop_count.str.replace(",", ""))

# Generate a list of ages 
age_lst = gen_age_col_lst()

# Get a datframe limited to the data ages columns only
age_df = slice_age_df(bham_pop_df, age_lst)

# Create a list of tuples of the start and finish indexes for the age bins
age_bins = get_col_bins(age_lst)

# get the ages in the age_df binned, and drop the original columns
age_df = bin_pop_ages(age_df, age_bins, age_lst)

# Ridding the bham pop df of the same cols
bham_pop_df.drop(age_lst, axis=1, inplace=True)

# merging summed+grouped ages back in
bham_pop_df = pd.merge(bham_pop_df, age_df, left_index=True, right_index=True)
# converting into GeoDataFrame
bham_pop_df = gpd.GeoDataFrame(bham_pop_df)

# create a buffer around the stops, in column "geometry" #forthedemo
# the `buffer_points` function changes the df in situ
_ = buffer_points(birmingham_stops_geo_df)
# TODO: Ask DataScience people why this is changed in situ

# renaming the column to geometry so the point in polygon func gets expected
bham_pop_df.rename(columns = {"geometry_pop": "geometry"}, inplace=True)

# import the disability data
# TODO: use new csv_to_df func to make disability_df
disability_df = pd.read_csv(os.path.join(CWD, "data", "nomis_QS303.csv"), header=5)
# drop the column "mnemonic" as it seems to be a duplicate of the OA code
# also "All categories: Long-term health problem or disability" is not needed, nor is
# "Day-to-day activities not limited"
drop_lst = ["mnemonic",
            "All categories: Long-term health problem or disability",
            "Day-to-day activities not limited"]
disability_df.drop(drop_lst, axis=1, inplace=True)
# the col headers are database unfriendly. Defining their replacement names
replacements = {"2011 output area":'OA11CD',
                "Day-to-day activities limited a lot":"disab_ltd_lot",
                "Day-to-day activities limited a little":"disab_ltd_little"}
# renaming the dodgy col names with their replacements
disability_df.rename(columns=replacements, inplace=True)

# Summing the two columns to get total disabled (which is what I thought
#   "All categories:..." was!)
disability_df["disb_total"] = disability_df["disab_ltd_lot"] + disability_df["disab_ltd_little"]

# Merge the disability df into main the pop df with a left join 
bham_pop_df = bham_pop_df.merge(disability_df, on='OA11CD', how="left")

# import the sex data
# TODO: use new csv_to_df func to make the sex_df
sex_df = pd.read_csv(os.path.join(CWD, "data", "nomis_QS104EW.csv"), header=6, usecols=["2011 output area", "Males", "Females"])
replacements = {"2011 output area":'OA11CD',
                "Males":"male",
                "Females":"female"}

# # renaming the dodgy col names with their replacements
sex_df.rename(columns=replacements, inplace=True)

# merge the sex data with the rest of the population data
bham_pop_df = bham_pop_df.merge(sex_df, on='OA11CD', how='left')

# find all the pop centroids which are in the bham_stops_poly
pop_in_poly_df = find_points_in_poly(bham_pop_df, birmingham_stops_geo_df)

# TODO: pop_in_poly_df has a lot of duplicates. Find out why
# Dropping duplicates
pop_in_poly_df.drop_duplicates(inplace=True)

# Count the population served by public transport
served = pop_in_poly_df.pop_count.sum()
full_pop = bham_pop_df.pop_count.sum()
not_served = full_pop - served
pct_not_served = "{:.2%}".format(not_served/full_pop)
pct_served = "{:.2%}".format(served/full_pop)

print(f"""The number of people who are served by public transport is {served}. \n 
        The full population of Birmingham is calculated as {full_pop}
        While the number of people who are not served is {not_served}""")


# Disaggregations!
pd.set_option("precision", 1)

# Calculating those served and not served by age
age_bins_ = ['0-4', '5-9', '10-14', '15-19', '20-24',
       '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55-59', '60-64',
       '65-69', '70-74', '75-79', '80-84', '85-89', '90+']

age_servd_df = served_proportions_disagg(pop_df=bham_pop_df, 
                                      pop_in_poly_df=pop_in_poly_df,
                                      cols_lst=age_bins_)

# Setting the data types for the df
age_servd_df = age_servd_df.astype('int32')

print("\n\n==========Age Disaggregation===========\n\n")

print(age_servd_df)

# Calculating those served and not served by sex
sex_cols = ['male', 'female']

sex_servd_df = served_proportions_disagg(pop_df=bham_pop_df, 
                                      pop_in_poly_df=pop_in_poly_df,
                                      cols_lst=sex_cols)

# Setting the data types for the df
sex_servd_df = sex_servd_df.astype('int32')

print("\n\n==========Sex Disaggregation===========\n\n")

print(sex_servd_df)

# Calculating those served and not served by disability
disab_cols = ["disab_ltd_lot", "disab_ltd_little", "disb_total"]

disab_servd_df = served_proportions_disagg(pop_df=bham_pop_df, 
                                      pop_in_poly_df=pop_in_poly_df,
                                      cols_lst=disab_cols)

# Setting the data types for the df
disab_servd_df = disab_servd_df.astype('int32')

print("\n\n==========Disability Disaggregation===========\n\n")

print(disab_servd_df)

# Calculating those served and not served by urban/rural
urb_col = ["urb_rur_class"]

# Filtering by urban and rural to make 2 dfs 
urb_df = bham_pop_df[bham_pop_df.urb_rur_class == "urban"]
rur_df = bham_pop_df[bham_pop_df.urb_rur_class == "rural"]

# Because these dfs a filtered to fewer rows, the pop_in_poly_df must be
# filtered in the same way
urb_pop_in_poly_df = (urb_df.merge(pop_in_poly_df,
                    on="OA11CD", how="left")
                    .loc[:,['OA11CD','pop_count_y']])
urb_pop_in_poly_df.rename(columns={'pop_count_y':'pop_count'}, inplace=True)
rur_pop_in_poly_df = (rur_df.merge(pop_in_poly_df, 
                    on="OA11CD", how="left")
                    .loc[:,['OA11CD','pop_count_y']])
rur_pop_in_poly_df.rename(columns={'pop_count_y':'pop_count'}, inplace=True)

urb_servd_df = served_proportions_disagg(pop_df=urb_df, 
                                      pop_in_poly_df=urb_pop_in_poly_df,
                                      cols_lst=['pop_count'])

rur_servd_df = served_proportions_disagg(pop_df=rur_df, 
                                      pop_in_poly_df=rur_pop_in_poly_df,
                                      cols_lst=['pop_count'])

urb_servd_df = urb_servd_df.astype('int32')
rur_servd_df = rur_servd_df.astype('int32')

print("\n\n==========Urban/Rural Disaggregation===========\n\n")

print(urb_servd_df)
print(rur_servd_df)