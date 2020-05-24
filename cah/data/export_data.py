""" Using the CAH API to export pack list and pack data to json files 
    from https://cah.greencoaststudios.com/ """

import requests
import json

PACK_LIST_URL = 'https://cah.greencoaststudios.com/api/v1/official/packs'
SINGLE_PACK_URL_BASE = 'https://cah.greencoaststudios.com/api/v1/official/'


def run_export():
    """ Retrieves a list of all CAH packs and then loops through the list
    to retrieve the pack contents 

    Does not return anything, but saves list and pack contents to files """
    res = requests.get(PACK_LIST_URL)
    if res.status_code == 200:
        response = res.json()
    else:
        print("Could not retrieve list of CAH packs. from")
        return

    with open("cah_pack_list.json", "w+") as file:
        file.write(json.dumps(response))

    decks = []
    for r in response.get('packs'):
        res = requests.get(SINGLE_PACK_URL_BASE + r.get('id'))
        if res.status_code == 200:
            decks.append(res.json())

    d = {'pack_contents':decks}
    with open("cah_packs.json", "w+") as file:
        file.write(json.dumps(d))


if __name__ == '__main__':
    run_export()
