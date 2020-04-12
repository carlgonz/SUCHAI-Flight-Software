import sys
import requests
import pandas as pd


def get_tle(row):
    url = "https://celestrak.com/satcat/tle.php?CATNR={}".format(row["catalog"])
    tle = requests.get(url)
    name, tle1, tle2, _ = tle.text.split('\r\n')
    print(name, row["name"])
    assert(name.rstrip() == row["name"])
    row["tle1"] = tle1
    row["tle2"] = tle2
    return row


filename = sys.argv[1]
sats = pd.read_csv(filename)
tles = sats.apply(get_tle, axis=1)
print(tles)
tles.to_csv(filename+".tle.csv", index=False)
