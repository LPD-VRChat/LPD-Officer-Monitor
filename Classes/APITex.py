import numpy as np
from array2gif import write_gif


#########################################################
### See bottom of file for GIF bitvalue documentation ###
#########################################################

def render_array(input, filename=None, w=8, h=8):
    
    if filename == None:
        real_filename = '/tmp/APITextemp.gif'
    else:
        real_filename = filename

    _white_value_RGB   = np.array([255, 255, 255])
    _black_value_RGB   = np.array([  0,   0,   0])
    _red_value_RGB     = np.array([255,   0,   0])
    _green_value_RGB   = np.array([  0, 255,   0])
    _blue_value_RGB    = np.array([  0,   0, 255])
    _yellow_value_RGB  = np.array([255, 255,   0])
    _cyan_value_RGB    = np.array([  0, 255, 255])
    _magenta_value_RGB = np.array([255,   0, 255])

    # This creates an array of arbitrary size based on the WxH size received on initialization.

    i = 0
    j = 0
    _base_row = []
    _base_array = []

    while j in range(0,w):
        _base_row.append(_black_value_RGB)
        j += 1
    
    while i in range(0,h):
        _base_array.append(_base_row)
        i += 1

    dataset = np.array(_base_array)
    
    z = w - 1

    dataset[0][z] = _white_value_RGB

    
    
    # In this section, we take the input dictionary and break it down into each value.
    # For adding bits, keep in mind that Udon starts at the bottom left, while python
    # starts at the top left. 
    # 
    # If you want to add values, do so here. Black is true White is false

    dataset[0][0] = _white_value_RGB if input["is_lpd"] and input["is_cadet"] else _black_value_RGB
    dataset[0][1] = _white_value_RGB if input["is_lpd"] and input["is_white_shirt"] else _black_value_RGB
    dataset[0][2] = _white_value_RGB if input["is_lpd"] and input["is_lpd"] else _black_value_RGB
    dataset[0][3] = _white_value_RGB if input["is_lpd"] and input["is_moderator"] else _black_value_RGB
    dataset[0][4] = _black_value_RGB
    dataset[0][5] = _black_value_RGB
    dataset[0][6] = _black_value_RGB
    dataset[0][7] = _black_value_RGB
    
    dataset[1][0] = _white_value_RGB if input["is_lpd"] and input["is_slrt"] else _black_value_RGB
    dataset[1][1] = _white_value_RGB if input["is_lpd"] and input["is_slrt_trainer"] else _black_value_RGB
    dataset[1][2] = _white_value_RGB if input["is_lpd"] and input["is_lmt"] else _black_value_RGB
    dataset[1][3] = _white_value_RGB if input["is_lpd"] and input["is_lmt_trainer"] else _black_value_RGB
    dataset[1][4] = _black_value_RGB
    dataset[1][5] = _black_value_RGB
    dataset[1][6] = _black_value_RGB
    dataset[1][7] = _black_value_RGB

    dataset[2][0] = _white_value_RGB if input["is_lpd"] and input["is_watch_officer"] else _black_value_RGB
    dataset[2][1] = _white_value_RGB if input["is_lpd"] and input["is_prison_trainer"] else _black_value_RGB
    dataset[2][2] = _white_value_RGB if input["is_lpd"] and input["is_instigator"] else _black_value_RGB
    dataset[2][3] = _white_value_RGB if input["is_lpd"] and input["is_trainer"] else _black_value_RGB
    dataset[2][4] = _black_value_RGB
    dataset[2][5] = _black_value_RGB
    dataset[2][6] = _black_value_RGB
    dataset[2][7] = _black_value_RGB

    dataset[3][0] = _white_value_RGB if input["is_lpd"] and input["is_chat_moderator"] else _black_value_RGB
    dataset[3][1] = _white_value_RGB if input["is_lpd"] and input["is_event_host"] else _black_value_RGB
    dataset[3][2] = _white_value_RGB if input["is_lpd"] and input["is_dev_team"] else _black_value_RGB
    dataset[3][3] = _white_value_RGB if input["is_lpd"] and input["is_media_production"] else _black_value_RGB
    dataset[3][4] = _black_value_RGB
    dataset[3][5] = _black_value_RGB
    dataset[3][6] = _black_value_RGB
    dataset[3][7] = _black_value_RGB

    dataset[4][0] = _white_value_RGB if input["is_lpd"] and input["is_janitor"] else _black_value_RGB
    dataset[4][1] = _white_value_RGB if input["is_lpd"] and input["is_korean"] else _black_value_RGB
    dataset[4][2] = _white_value_RGB if input["is_lpd"] and input["is_chinese"] else _black_value_RGB
    dataset[4][3] = _white_value_RGB if input["is_lpd"] and input["is_inactive"] else _black_value_RGB
    dataset[4][4] = _black_value_RGB
    dataset[4][5] = _black_value_RGB
    dataset[4][6] = _black_value_RGB
    dataset[4][7] = _black_value_RGB

    dataset[5][0] = _white_value_RGB if input["is_lpd"] and input["is_programming_team"] else _black_value_RGB
    dataset[5][1] = _black_value_RGB
    dataset[5][2] = _black_value_RGB
    dataset[5][3] = _black_value_RGB
    dataset[5][4] = _black_value_RGB
    dataset[5][5] = _black_value_RGB
    dataset[5][6] = _black_value_RGB
    dataset[5][7] = _black_value_RGB

    dataset[6][0] = _black_value_RGB
    dataset[6][1] = _black_value_RGB
    dataset[6][2] = _black_value_RGB
    dataset[6][3] = _black_value_RGB
    dataset[6][4] = _black_value_RGB
    dataset[6][5] = _black_value_RGB
    dataset[6][6] = _black_value_RGB
    dataset[6][7] = _black_value_RGB

    dataset[7][0] = _red_value_RGB   ############### WARNING: We can't reliably check this value in an 8x8
    dataset[7][1] = _black_value_RGB
    dataset[7][2] = _black_value_RGB
    dataset[7][3] = _black_value_RGB
    dataset[7][4] = _black_value_RGB
    dataset[7][5] = _black_value_RGB
    dataset[7][6] = _black_value_RGB
    dataset[7][7] = _black_value_RGB


    # Save the GIF
    write_gif(dataset, real_filename)







# This is the documentation for the LPD Officer Monitor's VRChatVideoPlayer integration.

# In order to gather permissions for a VRChat user, VRChat must first send a request
# for a video file, with the username in the url parameters.

# This bot will then grab permissions for that user, then use this module to generate a
# single frame GIF from the permissions table. This GIF must always be an 8x8 single frame.

# The bot then converts the GIF to a webm, which is returned to the video player. The Udon
# code then interprets that frame to get the RGB color values of the image.

# Currently this is just a binary system, with each pixel having a value of _black_value_RGB
# for False, and _white_value_RGB for True. Functionality will later be added for multi-state
# values, utilizing other colors.