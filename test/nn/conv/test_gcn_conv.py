import torch
from torch_sparse import SparseTensor
from torch_geometric.nn import GCNConv


def test_gcn_conv():
    x = torch.randn(4, 16)
    edge_index = torch.tensor([[0, 0, 0, 1, 2, 3], [1, 2, 3, 0, 0, 0]])
    row, col = edge_index
    value = torch.rand(row.size(0))
    adj2 = SparseTensor(row=row, col=col, value=value, sparse_sizes=(4, 4))
    adj1 = adj2.set_value(None)

    conv = GCNConv(16, 32)
    assert conv.__repr__() == 'GCNConv(16, 32)'
    out1 = conv(x, edge_index)
    assert out1.size() == (4, 32)
    assert torch.allclose(conv(x, adj1.t()), out1, atol=1e-6)
    out2 = conv(x, edge_index, value)
    assert out2.size() == (4, 32)
    assert torch.allclose(conv(x, adj2.t()), out2, atol=1e-6)

    t = '(Tensor, Tensor, OptTensor) -> Tensor'
    jit = torch.jit.script(conv.jittable(t))
    assert jit(x, edge_index).tolist() == out1.tolist()
    assert jit(x, edge_index, value).tolist() == out2.tolist()

    t = '(Tensor, SparseTensor, OptTensor) -> Tensor'
    jit = torch.jit.script(conv.jittable(t))
    assert torch.allclose(conv(x, adj1.t()), out1, atol=1e-6)
    assert torch.allclose(conv(x, adj2.t()), out2, atol=1e-6)


def test_sparse_node_feature_gcn_conv():
    x = torch.sparse_coo_tensor(indices=torch.tensor([[0, 0], [0, 1]]),
                                values=torch.tensor([1., 1.]),
                                size=torch.Size([4, 16]))
    edge_index = torch.tensor([[0, 0, 0, 1, 2, 3], [1, 2, 3, 0, 0, 0]])

    conv = GCNConv(16, 32)
    assert conv(x, edge_index).size() == (4, 32)


def test_static_gcn_conv():
    x = torch.randn(3, 4, 16)
    edge_index = torch.tensor([[0, 0, 0, 1, 2, 3], [1, 2, 3, 0, 0, 0]])

    conv = GCNConv(16, 32)
    out = conv(x, edge_index)
    assert out.size() == (3, 4, 32)
