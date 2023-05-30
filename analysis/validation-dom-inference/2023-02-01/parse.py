#!/usr/bin/env python3

import json
import statistics
import sys
from urllib.parse import urlparse

# import dom inference csv
#
# example line:
# 1000,2023-02-01T08:16:15.248Z,https://www.michaels.com,https://www.michaels.com/,1000-https!www.michaels.com-20230201081615250-0.png,1000-https!www.michaels.com-20230201081615250-1.png,1000-https!www.michaels.com-20230201081615250-0.html.gz,1000-https!www.michaels.com-20230201081615250-1.html.gz,0,0,0,0,0,0,0,0,0,0

data_dom = dict()
with open('websites-2023-02-01.csv', 'r') as f:
    for line in f.readlines():
        line = line.strip().split(',')

        # we only want to get the hostname
        website = urlparse(line[2]).hostname

        first     = int(line[8])
        amazon    = int(line[9])
        apple     = int(line[10])
        github    = int(line[11])
        google    = int(line[12])
        facebook  = int(line[13])
        linkedin  = int(line[14])
        microsoft = int(line[15])
        twitter   = int(line[16])
        yahoo     = int(line[17])

        print(f"{website} {first} {amazon}")

        data_dom[website] = {
            'first': first,
            'amazon': amazon,
            'apple': apple,
            'github': github,
            'google': google,
            'facebook': facebook,
            'linkedin': linkedin,
            'microsoft': microsoft,
            'twitter': twitter,
            'yahoo': yahoo,
        }

# import labeled_user.json
#
# categories:
# ["1st", "Amazon", "Apple", "Github", "Google", "Facebook", "Linkedin",
# "Microsoft", "Twitter", "Yahoo", "Other", "Meta-broken",
# "Meta-nonenglish", "Meta-nosso", "Meta-recrawl", "Cat-fin",
# "Cat-shop", "Cat-ent", "Cat-soc", "Cat-news", "Cat-lifestyle",
# "Cat-health", "Cat-bizserv", "Cat-info", "Cat-xxx"]
#
# we should skip anything that's Meta-broken, Meta-nonenglish,
# Meta-recrawl (don't consider it in our confusion matrix)
#
# for "Meta-nosso", that means all categories should be zeroed out
with open('labeled_user.json', 'r') as f:
    json_labeled = json.load(f)

data_labeled = dict()

# some counters
meta_skipped = 0
meta_nosso = 0
meta_sso = 0

for key in json_labeled.keys():
    # 1000-https!cardgames.io-20230201094318999-combined.png
    #print(key)

    # get the domain only in a wonderfully inefficient way:
    #
    # we can hardcode this because the suffix format of the key is
    # always going to be the same ("-{timestamp}-combined.png")
    key_clean = (key.split('!', 1)[1])[:-len("-20230201094318999-combined.png")]
    #print(key)

    values = json_labeled[key]

    if any( x in ["Meta-nonenglish", "Meta-broken", "Meta-recrawl"] for x in values ):
        # skip entry and move on
        meta_skipped += 1
        print(f"skipping {key_clean}")
        continue
    elif "Meta-nosso" in values:
        meta_nosso += 1
        print(f"no sso: {key_clean}")
        data_labeled[key_clean] = {
            'first': 0,
            'amazon': 0,
            'apple': 0,
            'github': 0,
            'google': 0,
            'facebook': 0,
            'linkedin': 0,
            'microsoft': 0,
            'twitter': 0,
            'yahoo': 0,
        }
    else:
        meta_sso += 1
        print(f"sso: {key_clean}")

        # ["1st", "Amazon", "Apple", "Github", "Google", "Facebook", "Linkedin", "Microsoft", "Twitter", "Yahoo", "Other"]
        # we ignore "Other"
        first     = 1 if "1st" in values else 0
        amazon    = 1 if "Amazon" in values else 0
        apple     = 1 if "Apple" in values else 0
        github    = 1 if "Github" in values else 0
        google    = 1 if "Google" in values else 0
        facebook  = 1 if "Facebook" in values else 0
        linkedin  = 1 if "Linkedin" in values else 0
        microsoft = 1 if "Microsoft" in values else 0
        twitter   = 1 if "Twitter" in values else 0
        yahoo     = 1 if "Yahoo" in values else 0

        data_labeled[key_clean] = {
            'first': first,
            'amazon': amazon,
            'apple': apple,
            'github': github,
            'google': google,
            'facebook': facebook,
            'linkedin': linkedin,
            'microsoft': microsoft,
            'twitter': twitter,
            'yahoo': yahoo,
        }


print(f"total: {len(json_labeled)}, skip: {meta_skipped}, nosso: {meta_nosso}, sso: {meta_sso}")

print(data_labeled)

meta_correct = list()
meta_TPR = list()  # sensitivity,recall
meta_FNR = list()  # miss rate
meta_FPR = list()  # false positive rate
meta_TNR = list()  # specificity

# quickly check that all keys match
meta_dominference_fail = 0
for key in data_labeled.keys():
    if key not in data_dom.keys():
        meta_dominference_fail += 1
        print(f"{key} not found in data_dom, skipping")
    else:
        print(f"analyzing {key}")
        TP = 0
        FP = 0
        TN = 0
        FN = 0

        values_labeled = data_labeled[key]
        values_dom     = data_dom[key]

        print(f"actual: {values_labeled}")
        print(f"predicted: {values_dom}")

        # now check whether actual == predicted
        keys_to_check = values_labeled.keys()
        keys_to_check = ["first"] # check only for first party

        # check only for SSO
        #keys_to_check = list(values_labeled.keys())
        #keys_to_check.remove("first")

        for sso_provider in keys_to_check:
            actual = values_labeled[sso_provider]
            predicted = values_dom[sso_provider]

            if actual == 1:
                if predicted == 1:
                    TP += 1
                elif predicted == 0:
                    FN += 1
            elif actual == 0:
                if predicted == 1:
                    FP += 1
                elif predicted == 0:
                    TN += 1

        P = TP + FN
        N = FP + TN

        print(f"positive: {P} negative: {N}")

        num_correct = TP + TN
        num_total   = P + N

        percent_correct = num_correct / num_total
        print(f"percent correct: {percent_correct}")

        meta_correct.append(percent_correct)

        # issues with divide by 0

        if P != 0:
            TPR = TP / P  # recall/sensitivity
            FNR = FN / P  # miss rate

            meta_TPR.append(TPR)
            meta_FNR.append(FNR)

        if N != 0:
            FPR = FP / N  # false positive rate
            TNR = TN / N  # specificity

            meta_FPR.append(FPR)
            meta_TNR.append(TNR)

        #F1 = (2 * TP) / ( ( 2 * TP ) + FP + FN )

print(f"{meta_correct}")
print(f"{sum(meta_correct) / len(meta_correct)}")
print(f"correctness median: {statistics.median(meta_correct)} mean: {statistics.mean(meta_correct)} length: {len(meta_correct)}")
print(f"correctness quantiles: {statistics.quantiles(meta_correct, n=10)}")

print(f"TPR median: {statistics.median(meta_TPR)} mean: {statistics.mean(meta_TPR)} length: {len(meta_TPR)}")
print(f"FNR median: {statistics.median(meta_FNR)} mean: {statistics.mean(meta_FNR)} length: {len(meta_FNR)}")
print(f"FPR median: {statistics.median(meta_FPR)} mean: {statistics.mean(meta_FPR)} length: {len(meta_FPR)}")
print(f"TNR median: {statistics.median(meta_TNR)} mean: {statistics.mean(meta_TNR)} length: {len(meta_TNR)}")


# now load logo template matching
print()
print()
print()
print()
data_templatematch = dict()

sso_supported = ['amazon',
                'apple',
                'github',
                'google',
                'facebook',
                'linkedin',
                'microsoft',
                'twitter',
                'yahoo',
                ]

with open('output-templatematch-2023-02-01.txt', 'r') as f:
    for line in f.readlines():
        # 1000-https!www.priceline.com-20230201102900088-1.png,facebook,facebook-20.jpg,0.951379
        line = line.strip().split(',')

        key = line[0]
        sso_detected = line[1].strip().lower()

        key_clean = (key.split('!', 1)[1])[:-len("-20230201094318999-1.png")]

        # supports only the following
        #   'google': (255, 0, 0),   # red
        #   'facebook': (0, 255, 0), # green
        #   'apple': (0, 0, 255),    # blue
        #   'github': (255, 128, 0), # orange
        #   'twitter': (255, 0, 255), # pink
        #   'microsoft': (153, 51, 255), # purple
        #   'linkedin': (255, 255, 0),  # yellow
        #   'amazon': (51, 255, 255) # aqua

        # add initial entry to dict
        if key_clean not in data_templatematch.keys():
            data_templatematch[key_clean] = {
                'amazon': 0,
                'apple': 0,
                'github': 0,
                'google': 0,
                'facebook': 0,
                'linkedin': 0,
                'microsoft': 0,
                'twitter': 0,
                'yahoo': 0,
            }

        if sso_detected in sso_supported:
            (data_templatematch[key_clean])[sso_detected] = 1
        elif sso_detected not in sso_supported:
            print(f"detected {sso_detected} but not in sso_supported -- bug?")

print(f"data_templatematch: {len(data_templatematch)} sites")

meta_correct = list()
meta_TPR = list()  # sensitivity,recall
meta_FNR = list()  # miss rate
meta_FPR = list()  # false positive rate
meta_TNR = list()  # specificity

# quickly check that all keys match
meta_templatematch_fail = 0
meta_templatematch_fail_sso = 0
for key in data_labeled.keys():
    if key not in data_templatematch.keys():
        meta_templatematch_fail += 1
        print(f"{key} not found in data_templatematch, skipping")

        # did the site _have_ SSO providers and templatematch failed to
        # find them?
        values_labeled = data_labeled[key]
        values_labeled_filtered = {key: values_labeled[key] for key in sso_supported}

        if 1 in values_labeled_filtered.values():
            print(f"{key} had an SSO that templatematch didn't find!")
            meta_templatematch_fail_sso += 1

    else:
        print(f"analyzing {key}")
        TP = 0
        FP = 0
        TN = 0
        FN = 0

        values_labeled       = data_labeled[key]
        values_templatematch = data_templatematch[key]

        print(f"actual: {values_labeled}")
        print(f"predicted: {values_templatematch}")

        # now check whether actual == predicted
        keys_to_check = values_templatematch.keys() # check only for SSO, and only for sites we support (see `sso_supported`)

        for sso_provider in keys_to_check:
            actual = values_labeled[sso_provider]
            predicted = values_templatematch[sso_provider]

            if actual == 1:
                if predicted == 1:
                    TP += 1
                elif predicted == 0:
                    FN += 1
            elif actual == 0:
                if predicted == 1:
                    FP += 1
                elif predicted == 0:
                    TN += 1

        P = TP + FN
        N = FP + TN

        print(f"positive: {P} negative: {N}")

        num_correct = TP + TN
        num_total   = P + N

        percent_correct = num_correct / num_total
        print(f"percent correct: {percent_correct}")

        meta_correct.append(percent_correct)

        # issues with divide by 0

        if P != 0:
            TPR = TP / P  # recall/sensitivity
            FNR = FN / P  # miss rate

            meta_TPR.append(TPR)
            meta_FNR.append(FNR)

        if N != 0:
            FPR = FP / N  # false positive rate
            TNR = TN / N  # specificity

            meta_FPR.append(FPR)
            meta_TNR.append(TNR)

        #F1 = (2 * TP) / ( ( 2 * TP ) + FP + FN )

print(f"{meta_correct}")
print(f"{sum(meta_correct) / len(meta_correct)}")
print(f"correctness median: {statistics.median(meta_correct)} mean: {statistics.mean(meta_correct)} length: {len(meta_correct)}")
print(f"correctness quantiles: {statistics.quantiles(meta_correct, n=10)}")

print(f"TPR median: {statistics.median(meta_TPR)} mean: {statistics.mean(meta_TPR)} length: {len(meta_TPR)}")
print(f"FNR median: {statistics.median(meta_FNR)} mean: {statistics.mean(meta_FNR)} length: {len(meta_FNR)}")
print(f"FPR median: {statistics.median(meta_FPR)} mean: {statistics.mean(meta_FPR)} length: {len(meta_FPR)}")
print(f"TNR median: {statistics.median(meta_TNR)} mean: {statistics.mean(meta_TNR)} length: {len(meta_TNR)}")

print(f"{(meta_templatematch_fail_sso)} {(meta_templatematch_fail)}")

if True:
    sys.exit(0)



import matplotlib.pyplot as plt

# histogram of correctness
plt.hist(
    meta_correct,
    bins=1000,
    density=True,
    histtype="step",
    cumulative=True,
    lw=5,
    label=f"hi"
)
plt.title("correct")
plt.show()

# histogram of TPR
#plt.hist(
#    meta_TPR,
#    bins=1000,
#    density=True,
#    histtype="step",
#    cumulative=True,
#    lw=5,
#    label=f"hi"
#)
#plt.title("TPR")
#plt.show()
