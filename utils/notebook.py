__author__ = 'andrey'


def print_stats(items):
    print("\n%-50s (%02d)" % (items[0].__class__.__name__ + "s", len(items)))
    for t in set(i.type for i in items):
        print("\ttype: %-35s  (%02d)" % (t, len([1 for i in items if i.type == t])))


def print_metadata_table(section):
    import matplotlib.pyplot as plt
    columns = ['Name', 'Value', 'Unit']
    cell_text = []
    for p in [(i.name, i) for i in section.props]:
        
        for i, v in enumerate(p[1].values):
            value = str(v.value)
            if len(value) > 30:
                value = value[:30] + '...'
            if i == 0:
                row_data = [p[0], value, p[1].unit if p[1].unit else '-']
            else:
                row_data = [p[0], value, p[1].unit if p[1].unit else '-']

            cell_text.append(row_data)
    if len(cell_text) > 0:
        nrows, ncols = len(cell_text)+1, len(columns)
        hcell, wcell = 1., 5.
        hpad, wpad = 0.5, 0    
        fig = plt.figure(figsize=(ncols*wcell+wpad, nrows*hcell+hpad))
        ax = fig.add_subplot(111)
        ax.axis('off')
        the_table = ax.table(cellText=cell_text,
                               colLabels=columns, 
                               loc='center')
        for cell in the_table.get_children():
            cell.set_height(.075)
            cell.set_fontsize(12)
                        
    #ax.set_title(section.name, fontsize=12)
    return fig
