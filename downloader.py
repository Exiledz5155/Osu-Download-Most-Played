import requests
import numpy as np
from osudbParser import readHeader, readBeatmap

def getMostPlayed(playerID : int, client_id : int, client_secret : str, count : int = 100) -> None:
    API_URL = 'https://osu.ppy.sh/api/v2'
    TOKEN_URL = 'https://osu.ppy.sh/oauth/token'
    def get_token():
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'public'
        }
        
        response = requests.post(TOKEN_URL, data=data)
        return response.json().get('access_token')

    token = get_token()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    params = {
        'mode': 'osu',
        'offset': 0,
        'limit': 100,
    }

    idArray = np.empty(count, np.uint32)
    session = requests.session()

    for i in range(0, count, 100):
        params['offset'] = i
        params['limit'] = i+100
        if count - i < 100:
            params['limit'] = i+count-i

        response = session.get(f'{API_URL}/users/{playerID}/beatmapsets/most_played', params=params, headers=headers).json()

        #response = session.get(f'{API_URL}/users/{playerID}/beatmaps', params=params, headers=headers).json()
        
        print(response)

        for counter, resp in enumerate(response):
            mapID = resp.get('beatmap_id')
            idArray[counter+i] = mapID

    datatype = np.dtype([("hash", np.dtype("<S32")), (("id"), (np.uint32))])
    beatmap = np.empty(count, dtype=datatype)
    mapC = 0
    i = 0
    arraySize = idArray.size // 50
    if arraySize == 0:
        arraySize = 50
    while i < arraySize:

        mapCounter = i * 50 + 50
        
        params['ids[]'] = idArray[i*50:mapCounter]
        
        response = session.get(f'{API_URL}/beatmaps', params=params, headers=headers)
        
        response = response.json()

        for j in response.get("beatmaps"):
            beatmap[mapC]['id'] = j.get('beatmapset_id')
            beatmap[mapC]['hash'] = j.get('checksum')
            mapC += 1

        i += 1

    print("Grabbed top " + str(count) + " most played from user ID:" + str(playerID))
    np.save("beatmaps.npy", beatmap) 


def downloadBeatmapSet(setID: int, session: requests.session, forbidden : dict[int, int | None], downloadPath : str) -> None:
    #beatmapCount = 0
    mapFile = session.get(f"https://api.chimu.moe/v1/download/{setID}").content
    mapName = session.get(f"https://api.chimu.moe/v1/set/{setID}").json()

    mapName = f'{mapName.get("SetId")} {mapName.get("Artist")} - {mapName.get("Title")}'.translate(forbidden)

    with open(f"{downloadPath}{mapName}.osz", "wb") as f:
        f.write(mapFile)

    #beatmapCount += 1
    #print("Downloading Beatmap #" + str(beatmapCount) + " ...")


def parseHashFromOsuDB(file) -> np.ndarray:
    header = readHeader(file)
    size = header[5]
    hashs = np.empty(size, np.dtype("<S32"))
    for i in range(size):
        beatmap = readBeatmap(file)
        if beatmap[7]:
            hashs[i] = beatmap[7][1]

    print("Parsing Hash from Osu.db ...")

    return hashs


def parseHashId(file = "beatmaps.npy") -> np.ndarray:

    data = np.load(file)

    print("Parsing Hash ID ...")

    return data


def downloadMaps(osudbFile, downloadPath : str) -> None:

    beatmapCount = 0

    with open(osudbFile, "rb") as osudbFile:
        hashs = parseHashFromOsuDB(osudbFile)

    ids = parseHashId()

    forbidden = str.maketrans("<>:\"/\\|?*", "_________")
    session = requests.session()
    downloadedIDs = []
    for hash, id in ids:
        if np.where(hash == hashs)[0].size or id in downloadedIDs:
            continue
        
        downloadBeatmapSet(id, session, forbidden, downloadPath)
        downloadedIDs.append(id)
        beatmapCount = beatmapCount + 1
        print("Downloading Beatmap #" + str(beatmapCount) + " ...")

    print("Complete. Good luck Nerd.")


if __name__ == "__main__":
    player_ID = int(input("Enter the player ID number: "))
    getMostPlayed(player_ID, 21307, "aSpxubbSi2skoN4f6yayzObWJMREFNyhGoTDzECQ", 100)
    downloadMaps("C:\\Users\\Exiledz\\AppData\\Local\\osu!\\osu!.db", "C:\\Users\\Exiledz\\AppData\\Local\\osu!\\Songs\\")


