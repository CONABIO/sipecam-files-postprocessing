from moviepy.editor import *


def convert_video(file_to_convert,file_type):
    """
    Converts avi file to mp4 and leaves it 
    in the same location as the original file

    Params:
        file_to_convert (string):   The file to convert with
                                    full path to location

        file_type (string):         The extension of the type 
                                    to convert
    
    Returns:
        (None)
    """

    # load the videoclip
    clip = VideoFileClip(file_to_convert)

    # get the filename for the mp4 file
    dstfilename = file_to_convert[0 : len(file_to_convert) - 4] + "." + file_type

    # write the mp4 file
    clip.write_videofile(dstfilename)