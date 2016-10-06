import html, re


def standardize(string):
    tmp1 = string.strip().replace("…", "...").replace("–", "-").replace("—", "-")
    tmp2 = re.sub("\t+", " ", tmp1)
    tmp3 = html.unescape(tmp2)
    return tmp3


# Removes cycles.
def remove_cycles(string):
   return re.sub("\([Цц]икл\s[^)]*\)", "", string)
