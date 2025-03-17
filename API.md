# Dictionary API

The api to search for a word is based on the python module [dictionary_en_gcide](https://github.com/leafarlins/dictionary_en_gcide), that looks for a word and it's meaning. The dictionary data is based in the open project [GCIDE]().

## Endpoint

### Look up a word

To lookup a word in the dictionary. The response output is an example. The values "cs" and "syn" will not always be present.

- **URL**: `/api/{lang}/{word}`
- **Method**: `GET`
- **Parameters**:
  - `lang` (string): Language of the dictionary (e.g., `en`).
  - `word` (string): Word to look up.
- **Response**:
  ```json
    {
    "lang": "en",
    "word": "fasten",
    "data": {
        "entry": "fasten",
        "pos": [
        {
            "etymology": "[AS. f; akin to OHG. festin. See Fast, a.]",
            "part_of_speech": "v. t.",
            "definitions": [
            {
                "text": "To fix firmly; to make fast; to secure, as by a knot, lock, bolt, etc.; as, to fasten a chain to the feet; to fasten a door or window.",
                "examples": []
            },
            {
                "text": "To cause to hold together or to something else; to attach or unite firmly; to cause to cleave to something , or to cleave together, by any means; as, to fasten boards together with nails or cords; to fasten anything in our thoughts.",
                "examples": [
                "The words Whig and Tory have been pressed to the service of many successions of parties, with very different ideas fastened to them."
                ]
            },
            {
                "text": "To cause to take close effect; to make to tell; to lay on; as, to fasten a blow.",
                "examples": [
                "If I can fasten but one cup upon him."
                ]
            }
            ],
            "cs": "To fasten a charge upon or To fasten a crime upon, to make his guilt certain, or so probable as to be generally believed. -- To fasten one's eyes upon, to look upon steadily without cessation. Acts iii. 4.",
            "syn": "Syn. -- To fix; cement; stick; link; affix; annex."
        },
        {
            "etymology": "[L.]",
            "part_of_speech": "v. i.",
            "definitions": [
            {
                "text": "To fix one's self; to take firm hold; to clinch; to cling.",
                "examples": [
                "A horse leech will hardly fasten on a fish."
                ]
            }
            ]
        }
        ]
    }
    }
  ```