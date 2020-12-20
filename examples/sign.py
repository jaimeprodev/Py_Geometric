import os.path as osp
import sys

import torch
import torch.nn.functional as F
from torch.nn import Linear
from torch.utils.data import DataLoader
from torch_geometric.datasets import Flickr
import torch_geometric.transforms as T

K = 2
path = osp.join("/home/laurent/graph_data", 'Flickr')
transform = T.Compose([T.NormalizeFeatures(), T.SIGN(K,1,0.5)])
dataset = Flickr(path, transform=transform)

print()
print('==================')
print(f'Number of graphs: {len(dataset)}')
print(f'Number of features: {dataset.num_features}')
print(f'Number of classes: {dataset.num_classes}')

data = dataset[0]

print(data)
print('==============================================================')

print(f'Number of nodes: {data.num_nodes}')
print(f'Number of edges: {data.num_edges}')
print(f'Average node degree: {data.num_edges / data.num_nodes:.2f}')
print(f'Contains isolated nodes: {data.contains_isolated_nodes()}')
print(f'Contains self-loops: {data.contains_self_loops()}')
print(f'Is undirected: {data.is_undirected()}')


train_idx = data.train_mask.nonzero(as_tuple=False).view(-1)
val_idx = data.val_mask.nonzero(as_tuple=False).view(-1)
test_idx = data.test_mask.nonzero(as_tuple=False).view(-1)

train_loader = DataLoader(train_idx, batch_size=16 * 1024, shuffle=True)
val_loader = DataLoader(val_idx, batch_size=32 * 1024)
test_loader = DataLoader(test_idx, batch_size=32 * 1024)


class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.lins = torch.nn.ModuleList()
        for _ in range(K + 1):
            self.lins.append(Linear(dataset.num_node_features, 1024))
        self.lin = Linear((K + 1) * 1024, dataset.num_classes)

    def forward(self, xs):
        hs = []
        for x, lin in zip(xs, self.lins):
            h = lin(x).relu()
            h = F.dropout(h, p=0.5, training=self.training)
            hs.append(h)
        h = torch.cat(hs, dim=-1)
        h = self.lin(h)
        return h.log_softmax(dim=-1)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = Net().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)


def train():
    model.train()

    total_loss = total_examples = 0
    for idx in train_loader:
        xs = [data.x[idx].to(device)]
        xs += [data[f'x{i}'][idx].to(device) for i in range(1, K + 1)]
        y = data.y[idx].to(device)

        optimizer.zero_grad()
        out = model(xs)
        loss = F.nll_loss(out, y)
        loss.backward()
        optimizer.step()

        total_loss += float(loss) * idx.numel()
        total_examples += idx.numel()

    return total_loss / total_examples


@torch.no_grad()
def test(loader):
    model.eval()

    total_correct = total_examples = 0
    for idx in loader:
        xs = [data.x[idx].to(device)]
        xs += [data[f'x{i}'][idx].to(device) for i in range(1, K + 1)]
        y = data.y[idx].to(device)

        out = model(xs)
        total_correct += int((out.argmax(dim=-1) == y).sum())
        total_examples += idx.numel()

    return total_correct / total_examples


for epoch in range(1, 201):
    loss = train()
    train_acc = test(train_loader)
    val_acc = test(val_loader)
    test_acc = test(test_loader)
    print(f'Epoch: {epoch:03d}, Loss: {loss:.4f}, Train: {train_acc:.4f}, '
          f'Val: {val_acc:.4f}, Test: {test_acc:.4f}')
