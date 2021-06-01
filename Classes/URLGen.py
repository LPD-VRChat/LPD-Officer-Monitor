from urllib.parse import quote_plus as enc


def geturls(input, useDict=False, baseURL="https://devbox.lolipd.com/api/auth?W=8&H=8&vrcuser="):

    output = []
    outputDict = {}

    for username in input:
        encoded_username = enc(username)
        url = f"""{baseURL}{encoded_username}"""
        output.append(url)
        tempDict = {}
        tempDict['username'] = username
        tempDict['url'] = url
        outputDict[username] = tempDict

    if useDict: return outputDict
    return output
