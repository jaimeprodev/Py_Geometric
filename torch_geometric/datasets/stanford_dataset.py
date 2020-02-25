import os
import os.path as osp
import shutil
import numpy as np

import torch
from torch_geometric.data import Data, InMemoryDataset, download_url, extract_gz, extract_tar, extract_zip
from torch_geometric.data.makedirs import makedirs


def to_assoc(indices):
    assoc = {}
    count = 0
    for i in indices:
        assoc[i.item()] = count
        count += 1
    return assoc


def from_assoc(assoc, idx):
    try:
        return assoc[idx]
    except KeyError:
        return -1


def read_stanford_data(dir, name):
    list_dir = os.listdir(dir)
    if len(list_dir) == 1 and osp.isdir(osp.join(dir,list_dir[0])):
        dir = osp.join(dir, list_dir[0])

    if 'ego-' in name:
        files = [file for file in os.listdir(dir) if osp.isfile(osp.join(dir, file))]
        files.sort()

        data_list = []
        for i in range(5, len(files), 5):
            circles_file = files[i]
            edges_file = files[i+1]
            egofeat_file = files[i+2]
            feat_file = files[i+3]
            featnames_file = files[i+4]

            x = torch.from_numpy(np.loadtxt(osp.join(dir, feat_file))).long()
            indices = x[:,0]
            indices_assoc = to_assoc(indices)
            x = x[:,1:]

            circles = []
            f = open(osp.join(dir ,circles_file), "r")
            c_line = f.readline()
            while not c_line == '':
                circles.append([from_assoc(indices_assoc, int(i)) for i in c_line.split()[1:]])
                c_line = f.readline()
            f.close()

            edge_index = torch.from_numpy(np.loadtxt(osp.join(dir, edges_file)))\
                              .transpose(0,1).long()

            # TODO find more efficient way to do this
            for i in range(edge_index.shape[0]):
                for j in range(edge_index.shape[1]):
                    edge_index[i][j] = from_assoc(indices_assoc, edge_index[i][j].item())


            x_ego = torch.from_numpy(np.loadtxt(osp.join(dir, egofeat_file))).long()
            x = torch.cat((x, x_ego.unsqueeze(0)))

            # ego Node is connected so every other node
            edge_index_ego = torch.fill_(torch.zeros((2,x.shape[0]-1)), x.shape[0]-1)
            edge_index_ego[0] = torch.arange(x.shape[0]-1)

            # nodes undirected in ego-Facebook
            if name == 'ego-Facebook':
                edge_index_ego2 = torch.fill_(torch.zeros((2,x.shape[0]-1)), x.shape[0]-1)
                edge_index_ego2[1] = torch.arange(x.shape[0]-1)
                edge_index = torch.cat((edge_index,
                                        edge_index_ego.long(),
                                        edge_index_ego2.long()), dim=1)

            edge_index = torch.cat((edge_index, edge_index_ego.long()), dim=1)

            data = Data(x=x, edge_index=edge_index, circles=circles)
            data_list.append(data)
        return data_list

    elif 'soc-' in name:
        if name == 'soc-Pokec':
            #TODO? read out features from 'soc-pokec-profiles.txt'
            edge_index = torch.from_numpy(np.loadtxt(osp.join(dir, 'soc-pokec-relationships.txt')))\
                              .transpose(0,1).long()
            data = Data(edge_index=edge_index)
            return [data]
        else:
            list_dir = os.listdir(dir)
            if len(list_dir) == 1 and osp.isfile(osp.join(dir, list_dir[0])):
                edge_index = torch.from_numpy(np.loadtxt(osp.join(dir, list_dir[0])))\
                                  .transpose(0,1).long()
                # print(np.sum(np.unique(edge_index.numpy()) == np.arange(1, torch.max(edge_index).item()+2)))
                data = Data(edge_index=edge_index)
                return [data]


class StanfordDataset(InMemoryDataset):

    def __init__(self, root,  name, transform=None, pre_transform=None,
                 pre_filter=None, use_node_attr=False, use_edge_attr=False):

        self.url = 'https://snap.stanford.edu/data'
        self.available_datasets_file = {'ego-Facebook': ['facebook.tar.gz'],
                                        'ego-Gplus': ['gplus.tar.gz'],
                                        'ego-Twitter': ['twitter.tar.gz'],
                                        'soc-Epinions1': ['soc-Epinions1.txt.gz'],
                                        'soc-LiveJournal1': ['soc-LiveJournal1.txt.gz'],
                                        'soc-Pokec': ['soc-pokec-relationships.txt.gz',
                                                      'soc-pokec-profiles.txt.gz'],
                                        'soc-Slashdot0811': ['Slashdot0811.txt.gz'],
                                        'soc-Slashdot0922': ['Slashdot0902.txt.gz'],
                                        }
        available_datasets = list(self.available_datasets_file.keys())

        if name not in available_datasets:
            raise NameError('Name \'{}\' is not an available dataset. Try one of these {}.'.format(name, available_datasets))

        self.name = name
        super(StanfordDataset, self).__init__(root, transform, pre_transform, pre_filter)

        self.data_list = torch.load(self.processed_paths[0])

        '''
        self.data, self.slices = torch.load(self.processed_paths[0])

        if self.data.x is not None and not use_node_attr:
            self.data.x = self.data.x[:, self.num_node_attributes:]
        if self.data.edge_attr is not None and not use_edge_attr:
            self.data.edge_attr = self.data.edge_attr[:, self.num_edge_attributes:]
        '''

    def _download(self):
        print(self.raw_dir)
        if not osp.isdir(self.raw_dir):
            makedirs(self.raw_dir)
            self.download()
        elif len(os.listdir(self.raw_dir)) == 0:
            self.download()
        else:
            return


    def download(self):
        folder = osp.join(self.root, self.name)
        for file in self.available_datasets_file[self.name]:
            path = download_url('{}/{}'.format(self.url, file), folder)
            if file.endswith('.tar.gz'):
                extract_tar(path, folder)
            elif file.endswith('.gz'):
                extract_gz(path, folder)
            os.unlink(path)
        shutil.rmtree(self.raw_dir)
        os.rename(folder, self.raw_dir)


    @property
    def processed_file_names(self):
        return 'data.pt'


    def process(self):
        print(self.processed_paths[0])
        self.data_list = read_stanford_data(self.raw_dir, self.name)

        if self.pre_filter is not None:
            self.data_list = [data for data in self.data_list if self.pre_filter(data)]

        if self.pre_transform is not None:
            self.data_list = [self.pre_transform(data) for data in self.data_list]

        # torch.save(self.collate(self.data_list), self.processed_paths[0])
        torch.save(self.data_list, self.processed_paths[0])


    def get(self, idx):
        try:
            return self.data_list[idx]
        except IndexError:
            raise IndexError("Index out of bounds. Try an index <= {}".format(len(self.data_list)-1))


    def __repr__(self):
        return '{}({})'.format(self.name, len(self))


if __name__ == '__main__':
    # dataset_name = 'ego-Facebook'
    dataset_name = 'soc-Pokec'
    path = path = osp.join(osp.dirname(osp.realpath(__file__)), '..', '..', 'data', dataset_name)
    dataset = StanfordDataset(path, dataset_name)
    data = dataset[0]
    print(data)
