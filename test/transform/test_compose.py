import torch
import torch_geometric.transform as T
from torch_geometric.datasets.dataset import Data


def test_compose():
    transform = T.Compose([T.Cartesian(), T.TargetIndegree()])
    expected_output = ('Compose([\n'
                       '    Cartesian(cat=True),\n'
                       '    TargetIndegree(cat=True),\n'
                       '])')
    assert transform.__repr__() == expected_output

    pos = torch.tensor([[-1, 0], [0, 0], [2, 0]], dtype=torch.float)
    edge_index = torch.tensor([[0, 1], [1, 2]])
    data = Data(None, pos, edge_index, None, None)
    expected_output = [[0.75, 0.5, 1], [1, 0.5, 1]]

    data = transform(data)
    assert data.weight.tolist() == expected_output
