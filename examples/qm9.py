import os
import sys

sys.path.insert(0, '.')
sys.path.insert(0, '..')

from torch_geometric.datasets import QM9  # noqa
from torch_geometric.utils import DataLoader  # noqa

path = os.path.dirname(os.path.realpath(__file__))
path = os.path.join(path, '..', 'data', 'QM9')

train_dataset = QM9(path, train=True)
test_dataset = QM9(path, train=False)
train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=256)

for data in train_loader:
    data = data.cuda().to_variable()
