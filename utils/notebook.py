__author__ = 'andrey'


def print_stats(items):
    print("\n%-50s (%02d)" % (items[0].__class__.__name__ + "s", len(items)))
    for t in set(i.type for i in items):
        print("\ttype: %-35s  (%02d)" % (t, len([1 for i in items if i.type == t])))
