import json

def load_decks():
    with open("cah/data/cah_pack_list.json", "r") as file:
        all_decks = json.loads(file.read())
    return all_decks.get('packs')