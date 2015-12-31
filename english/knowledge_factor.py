# coding: utf-8

class KnowledgeFactor(object):

    def _tag_convert(self, tags):
        if isinstance(tags, dict):
            res = [(tag, float(d)) for tag, d in tags.iteritems()]
        elif isinstance(tags, list):
            res = [(tag, float(d)) for tag, d in tags]
        return dict(res)

    def __init__(self, ktags={}, rktags={}):
        self.ktags = self._tag_convert(ktags)
        self.rktags = self._tag_convert(rktags)

    @classmethod
    def merge(cls, kfactors):
        k_dict = {}
        rk_dict = {}
        for fac in kfactors:
            for tag, d in fac.ktags.iteritems():
                if tag not in k_dict:
                    k_dict[tag] = [0, 0]
                k_dict[tag][0] += d
                k_dict[tag][1] += 1
            for tag, d in fac.rktags.iteritems():
                if tag not in rk_dict:
                    rk_dict[tag] = [0, 0]
                rk_dict[tag][0] += d
                rk_dict[tag][1] += 1
        res = KnowledgeFactor()
        for tag, (d, cnt) in k_dict.iteritems():
            res.ktags[tag] = float(d) / cnt
        for tag, (d, cnt) in rk_dict.iteritems():
            res.rktags[tag] = float(d) / cnt
        return res

    def text(self):
        k_txt = ['1:'+str(ktag)+':'+str(d) for ktag,d in self.ktags.iteritems()]
        rk_txt = ['2:'+str(ktag)+':'+str(d) for ktag,d in self.rktags.iteritems()]
        return "|".join(k_txt + rk_txt)

    def difficulty(self):
        ds = self.ktags.values()
        return 0. if len(ds) == 0 else float(sum(ds)) / len(ds)

