import numpy as np

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
