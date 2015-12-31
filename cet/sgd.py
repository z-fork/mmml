# coding: utf-8

import numpy as np

fac_dim = 10
max_iter_num = 25
lambda_fac = 0.005
lambda_weight = 0.001
gamma = 0.08
step_desc = 0.9


def fac_norm(x):
    return np.sqrt(np.inner(x, x))


def average_fac(fac_list):
    fac = reduce(lambda x, y: x + y, fac_list)
    fac /= len(fac_list)
    return fac


def interpret(p, q, w, w0, d):
    return np.inner(w, p - q) + w0 * d


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def predict(p, q, w, w0, d):
    z = interpret(p, q, w, w0, d)
    z = sigmoid(z)
    return max(min(z, 1), 0)


def sgd_init(df):
    user_fac, item_fac = {}, {}
    users = df.uid.unique()
    questions = df.qid.unique()
    for uid in users:
        user_fac[uid] = np.random.normal(0, 1, fac_dim)
    for qid in questions:
        item_fac[qid] = np.random.normal(0, 1, fac_dim)
    w = np.random.normal(0, 1, fac_dim)
    w0 = np.random.normal(0, 1)
    return user_fac, item_fac, w, w0


def sgd_update(ufac, ifac, status, d, w, w0, gamma):
    p_u, q_i = ufac, ifac
    err = predict(p_u, q_i, w, w0, d) - status
    ufac1 = p_u - gamma * (err * w + lambda_fac * p_u)
    ifac1 = q_i - gamma * (err * (-w) + lambda_fac * q_i)
    w1 = w - gamma * (err * (p_u - q_i) + lambda_weight * w)
    w0_1 = w0 - gamma * (err * d + lambda_weight * w0)
    return ufac1, ifac1, w1, w0_1


def evaluate(user_fac, item_fac, w, w0, df):
    ufac0 = average_fac(user_fac.values())
    ifac0 = average_fac(item_fac.values())
    correct = 0
    for _, row in df.iterrows():
        uid, qid, status, d = row
        ufac = user_fac.get(uid, ufac0)
        ifac = item_fac.get(qid, ifac0)
        r = predict(ufac, ifac, w, w0, d)
        r = 1 if r >= 0.5 else 0
        #r = 1 if r >= 0 else -1
        if r == status:
            correct += 1
    return float(correct) / len(df)


def cost(user_fac, item_fac, w, w0, df):
    ans = 0.0
    for _, row in df.iterrows():
        uid, qid, y, d = row
        ufac = user_fac[uid]
        ifac = item_fac[qid]
        r = predict(ufac, ifac, w, w0, d)
        ans += 2 * (- y * np.log(r) - (1 - y) * np.log(1 - r))
    for uid, ufac in user_fac.iteritems():
        ans += lambda_fac * fac_norm(ufac) ** 2
    for qid, ifac in item_fac.iteritems():
        ans += lambda_fac * fac_norm(ifac) ** 2
    ans += lambda_weight * (np.inner(w, w) + w0 ** 2)
    return ans / 2


def irt_process(train, test, gamma=gamma):
    user_fac, item_fac, w, w0 = sgd_init(train)
    for num in xrange(max_iter_num):
        print 'iteration %d' % (num + 1)
        index = range(len(train))
        np.random.shuffle(index)
        for i in index:
            uid, qid, status, d = train.iloc[i]
            ufac = user_fac[uid]
            ifac = item_fac[qid]
            ufac1, ifac1, w1, w0_1 = sgd_update(ufac, ifac, status, d, w, w0, gamma)
            user_fac[uid] = ufac1
            item_fac[qid] = ifac1
            w = w1.copy()
            w0 = w0_1
        gamma *= step_desc
        print 'train cost: %.4f' % cost(user_fac, item_fac, w, w0, train)
        print 'train accuracy: %.4f' % evaluate(user_fac, item_fac, w, w0, train)
        accuracy = evaluate(user_fac, item_fac, w, w0, test)
        print 'test accuracy: %.4f' % accuracy
        print ''
    return user_fac, item_fac, w, w0, accuracy
