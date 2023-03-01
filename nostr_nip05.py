import json

nostr_json = {
    "jl1nie": "7d2180ecb3f0f16d9b50ab26644eeeaab233494f5a9d241a077b92cf45297fa7",
    "sotaspotja": "830195f597a967fac5ebbce20b7775626d909172daa6e5f8ca7397b92421744e",
    "potaspotja": "3e1691aa75beb6aff2887e677b10f89a5ab9f71e7e3c54800eb6ab96d3afd9a7",
    "js1yfc": "461f138f1c324940d6c3e67561b293e48140b0071c390a5b941b9e1f59aeb880",
}


def nostr_nip05(name):
    pubkey = nostr_json.get(name, "")
    return {
        "names": {
            name: pubkey
        }
    }


if __name__ == "__main__":
    print(json.dumps(nostr('jl1nie')))
    print(json.dumps(nostr('sotaspotja')))
    print(json.dumps(nostr('potaspotja')))
    print(json.dumps(nostr('js1yfc')))
