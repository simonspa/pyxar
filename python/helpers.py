import numpy as np
from copy import copy

def list_to_grid(n_cols,n_rows,a_list):
    """Helper function that converts a list from TB into a grid with rows and cols"""
    if len(a_list) != n_rows*n_cols:
        assert 'List with %s is not matching expected n_rows %s * n_cols= %s : %s' %(len(a_list),n_rows, n_cols, n_rows*n_cols)
    grid = [[0 for x in xrange(n_rows)] for x in xrange(n_cols)] 
    for i, value in enumerate(a_list):
        col = int(i/n_rows)
        row = int(i%n_rows)
        grid[col][row] = a_list[col * n_rows + row]
    return grid

def list_to_matrix(n_cols,n_rows,a_list):
    return np.array(list_to_grid(n_cols,n_rows,a_list))

def decode(n_cols, n_rows, address, a_list):
    s = (n_cols,n_rows)
    roc_data = np.zeros(s)
    for i, adr in enumerate(address):
        row = adr & 0xff
        col = (adr >> 8) & 0xff
        if ( (col >= n_cols or col < 0) or (row >= n_rows or row < 0)):
            #raise Exception("Adress: %s decoded (col,row) (%s,%s)"%(adr,col,row))
            print "Adress: %s decoded (col,row) (%s,%s)"%(hex(adr),col,row)
            col = 0
            row = 0
        roc_data[col][row] += a_list[i]
    return roc_data

def decode_full(n_rocs, n_cols, n_rows, address, a_list):
    s = (n_cols,n_rows)
    datas = []
    for i in range(n_rocs):
        datas.append(np.zeros(s))
    for i, adr in enumerate(address):
        row = adr & 0xff
        col = (adr >> 8) & 0xff
        roc = (adr >> 16) & 0xff
        tbm = (adr >> 24) & 0xff
        roc += tbm*8
        if ( (col >= n_cols or col < 0) or (row >= n_rows or row < 0) or (roc < 0 or roc >= n_rocs)):
            #raise Exception("Adress: %s decoded (col,row) (%s,%s)"%(adr,col,row))
            print "Adress: %s decoded (col,row) (%s,%s)"%(hex(adr),col,row)
            col = 0
            row = 0
        else:
            #print roc, col, row
            datas[roc][col][row] += a_list[i]
    return datas
