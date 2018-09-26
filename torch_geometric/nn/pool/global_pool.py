from torch_scatter import scatter_add, scatter_mean, scatter_max


def global_add_pool(x, batch, size=None):
    return scatter_add(x, batch, dim=0, dim_size=size)


def global_mean_pool(x, batch, size=None):
    return scatter_mean(x, batch, dim=0, dim_size=size)


def global_max_pool(x, batch, size=None):
    fill = -9999999
    return scatter_max(x, batch, 0, dim_size=size, fill_value=fill)[0]
