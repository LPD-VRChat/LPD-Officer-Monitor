from urllib.parse import quote_plus as enc


def geturls(input, baseURL="https://devbox.lolipd.com/api/auth?W=8&H=8&vrcuser="):

    output = []

    for username in input:
        encoded_username = enc(username)
        url = f"""{baseURL}{encoded_username}"""
        output.append(url)

    return output
