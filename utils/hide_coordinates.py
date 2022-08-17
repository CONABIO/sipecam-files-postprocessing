import json
import exiftool
import traceback


TAGS_FOR_GPS_COMPOSITE = {
    "Composite:GPSLatitude": "Composite:GPSLatitude",
    "Composite:GPSLongitude": "Composite:GPSLongitude",
    "Composite:GPSPosition": "GPSPosition"
}

TAGS_FOR_GPS_EXIF = {
    "EXIF:GPSLatitude": "EXIF:GPSLatitude",
    "EXIF:GPSLongitude": "EXIF:GPSLongitude",
    "EXIF:GPSLatitudeRef": "GPSLatitudeRef",
    "EXIF:GPSLongitudeRef": "GPSLongitudeRef",
}


def extract_gps(filename):
    gps_metadata = {}
    with exiftool.ExifToolHelper() as et:
        exiftool_metadata_gps_exif = et.get_tags(filename, TAGS_FOR_GPS_EXIF.keys())[0]

    with exiftool.ExifToolHelper() as et:
        exiftool_metadata_gps_composite = et.get_tags(
            filename, TAGS_FOR_GPS_COMPOSITE.keys()
        )[0]
    print()
    for k, v in TAGS_FOR_GPS_EXIF.items():
        try:
            gps_metadata[v] = exiftool_metadata_gps_exif[k]
        except Exception as e:
            pass
    for k, v in TAGS_FOR_GPS_COMPOSITE.items():
        try:
            gps_metadata[v] = exiftool_metadata_gps_composite[k]
        except Exception as e:
            pass
    return gps_metadata


def subs_lat_long(filename,lat,lng):
    with exiftool.ExifToolHelper() as et:
        et.set_tags(filename,
                    tags={"GPSLatitude": lat,
                          "GPSLongitude": lng},
                    params=["-P", "-overwrite_original"]
                   )


def hide_coordinates(f,json_file):
    """
    Hides coordinates in image metadata, replacing it
    with coordinates from cumulus.

    Params:
        f (string): File to hide coordinates
        json_file (string): Json file with extracted metadata

    Returns:
        (string or boolean):    A string with info of the replaced coordinates
                                or False if coordinates could not ber obfuscated
    """

    try:
        data_file = open(json_file)

        metadata = json.load(data_file)
    except:
        print("No json file with metadata in location, cannot obtain obfuscated coordinates.")

        return False
    try:
        obfuscated_lat = metadata["MetadataDevice"]["CentroidCumulusLatitude"]
        obfuscated_lng = metadata["MetadataDevice"]["CentroidCumulusLongitude"]

    except:
        print("Cannot obfuscate coordinates, not CentroidCumulus lat/lng coordinates in json file %s" % json_file)

        return False

    try:
        # checking current coordinates
        gps_dict = extract_gps(f)

        if len(gps_dict.keys()) > 0:
            # replacing current coordinates with obfuscated ones
            subs_lat_long(f,obfuscated_lat,obfuscated_lng)

            # replacing obfuscated coordinates
            return extract_gps(f)
        
        else:
            print("File doesn't have coordinates")
            
            # replacing current coordinates with obfuscated ones
            subs_lat_long(f,obfuscated_lat,obfuscated_lng)
            
            return extract_gps(f)
    
    except Exception as e:
        print(traceback.format_exc())
        print("Error extracting/setting coordinates in file metadata, error: ", e)

        return False