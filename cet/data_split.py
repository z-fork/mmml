# coding: utf-8

import pandas as pd
import numpy as np


def split_list(x, kfold):
    n = len(x)
    quo = n / kfold
    rem = n % kfold
    counts = [quo] * kfold
    counts[-1] += rem
    j = 0
    res = []
    for i in xrange(kfold):
        cnt = counts[i]
        res.append(x[j:(j + cnt)])
        j += cnt
    return res


def load_data(data_path):
    record = pd.read_csv(data_path, sep='\t', header=None)
    record.columns = ['subtype', 'subid', 'qtype', 'qid',
                      'uid', 'status', 'date', 'difficulty']
    ans = record[['subtype', 'subid', 'uid', 'status', 'difficulty']]
    # FXXK pandas, 跟 R 比你就是个未进化完全的东西
    new_qid = zip(map(str, ans.subtype), map(str, ans.subid))
    new_qid = map(lambda x: ":".join(x), new_qid)
    #new_qid = ans.apply(lambda x: str(x.subtype) + ':' + str(x.subid), axis=1)
    # FIXME weird warning
    ans['qid'] = new_qid[:]
    ans.status -= 1
    return ans[['uid', 'qid', 'status', 'difficulty']]


def split_data(df, kfold=5):
    idx = range(len(df))
    np.random.shuffle(idx)
    slices = split_list(idx, kfold)
    res = []
    for slice in slices:
        res.append(df.iloc[slice])
    return res


def split_data_by_user(df, kfold=5):
    df_group = df.groupby('uid')
    folds = []
    for i in xrange(kfold):
        folds.append([])
    for uid, group in df_group:
        res = split_data(group, kfold)
        for i in xrange(kfold):
            folds[i].append(res[i])
    return map(pd.concat, folds)


def make_data_set(data_path, kfold):
    record = load_data(data_path)
    return split_data_by_user(record, kfold)

