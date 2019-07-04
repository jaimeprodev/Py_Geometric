import torch
import pytest
from torch_geometric.nn import (global_add_pool, global_mean_pool,
                                global_max_pool)


def test_global_pool():
    N_1, N_2 = 4, 6
    x = torch.randn(N_1 + N_2, 4)
    batch = torch.tensor([0 for _ in range(N_1)] + [1 for _ in range(N_2)])

    out = global_add_pool(x, batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == x[:4].sum(dim=0).tolist()
    assert out[1].tolist() == x[4:].sum(dim=0).tolist()

    out = global_mean_pool(x, batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == x[:4].mean(dim=0).tolist()
    assert out[1].tolist() == x[4:].mean(dim=0).tolist()

    out = global_max_pool(x, batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == x[:4].max(dim=0)[0].tolist()
    assert out[1].tolist() == x[4:].max(dim=0)[0].tolist()


def test_permuted_global_pool():
    N_1, N_2 = 4, 6
    x = torch.randn(N_1 + N_2, 4)
    batch = torch.tensor([0 for _ in range(N_1)] + [1 for _ in range(N_2)])

    permutation = torch.randperm(N_1 + N_2)
    perm_x = x[permutation]
    perm_batch = batch[permutation]

    out = global_add_pool(perm_x, perm_batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == pytest.approx(x[:4].sum(dim=0).tolist())
    assert out[1].tolist() == pytest.approx(x[4:].sum(dim=0).tolist())

    out = global_mean_pool(perm_x, perm_batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == pytest.approx(x[:4].mean(dim=0).tolist())
    assert out[1].tolist() == pytest.approx(x[4:].mean(dim=0).tolist())

    out = global_max_pool(perm_x, perm_batch)
    assert out.size() == (2, 4)
    assert out[0].tolist() == pytest.approx(x[:4].max(dim=0)[0].tolist())
    assert out[1].tolist() == pytest.approx(x[4:].max(dim=0)[0].tolist())
