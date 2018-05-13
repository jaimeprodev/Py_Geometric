from pytest import approx
import torch
from torch_geometric.transform import Polar
from torch_geometric.datasets.dataset import Data


def test_polar():
    assert Polar().__repr__() == 'Polar(cat=True)'

    pos = torch.tensor([[-1, 0], [0, 0], [0, 2]], dtype=torch.float)
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]])
    data = Data(None, pos, edge_index, None, None)

    out = Polar()(data).weight.view(-1).tolist()
    assert approx(out) == [0.5, 0, 0.5, 0.5, 1, 0.25, 1, 0.75]

    data.weight = torch.tensor([1, 1, 1, 1], dtype=torch.float)
    out = Polar()(data).weight.view(-1).tolist()
    assert approx(out) == [1, 0.5, 0, 1, 0.5, 0.5, 1, 1, 0.25, 1, 1, 0.75]
