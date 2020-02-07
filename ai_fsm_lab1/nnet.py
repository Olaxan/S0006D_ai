# pip3 install torch torchvision
# pip3 install pytmx
# pip3 install pygame

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset
from tqdm import tqdm
from path import Path


class CustomDataset(Dataset):
    # A pytorch dataset class for holding data for a text classification task.

    def __init__(self, world, data_points):
        '''
        Takes as input the name of a file containing sentences with a classification label (comma separated) in each line.
        Stores the text data in a member variable X and labels in y
        '''

        self.world = world
        self.X, self.y = self.populate_dataset(data_points)

    def random_path(self):
        """Get a random A-star path in the world"""

        p1 = self.world.get_random_cell()
        p2 = self.world.get_random_cell()
        success, path, costs = Path.a_star_search(self.world.graph, p1, p2)
        cost = 0
        if success:
            for node in path:
                cost += costs[node]

        grid = [[0 for col in range(self.world.width)] for row in range(self.world.height)]
        grid[p1[0]][p1[1]] = 2
        grid[p2[0]][p2[1]] = 2

        return grid, cost #y??

    def populate_dataset(self, count):
        """Fill the dataset with random paths for training purposes"""

        x = []
        y = []
        for i in range(count):
            a, b = self.random_path()
            x = x + [a]
            y = y + [b]
        return (x, y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, index):
        return torch.FloatTensor(self.X[index]),self.y[index]

class Net(nn.Module):

    def __init__(self, input_size, output_size=10):
        super().__init__()
        self._input_size = input_size
        self._output_size = output_size
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 64)
        self.fc4 = nn.Linear(64, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return F.log_softmax(x, dim=1)

    @property
    def input_size(self):
        return self._input_size

    @property
    def output(self):
        return self._output_size

class NeuralHeuristic:

    loss_function = torch.nn.CrossEntropyLoss()
    optimizer = optim.Adam

    def __init__(self, world, data_points, train_batch=200, test_batch=10):
        self.net = Net(world.height * world.width)
        self.optimizer = self.optimizer(self.net.parameters(), lr=0.001)
        self.train_batch = train_batch
        self.test_batch = test_batch
        train_data = CustomDataset(world, data_points)
        test_data = CustomDataset(world, data_points)
        train_set = torch.utils.data.DataLoader(train_data, train_batch, shuffle=True)
        test_set = torch.utils.data.DataLoader(test_data, test_batch, shuffle=False)
        self.train(train_set, test_set)

    def train(self, train_set, test_set):

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print('Training net on {}'.format(device))

        self.net.to(device)

        #Teach the NN
        for epoch in range(self.train_batch):
            for data in tqdm(train_set):    # 'data' is a batch of data
                X, y = data                 # X is the batch of features, y is the batch of targets
                self.net.zero_grad()        # sets gradients to 0 before loss calc
                X = X.to(device)
                output = self.net(X.view(-1, self.net.input_size))      # pass in the reshaped batch
                output = output.cpu()
                loss = self.loss_function(output, y)    # calc and grab the loss value
                loss.backward()                         # apply this loss backwards thru the network's parameters
                self.optimizer.step()                   # attempt to optimize weights to account for loss/gradients
            self.net = self.net.to(device)
            correct = 0
            total = 0
            with torch.no_grad():
                for data in tqdm(test_set):
                    X, y = data
                    X = X.to(device)
                    output = self.net(X.view(-1, self.net.input_size))
                    output = output.cpu()
                    for idx, i in enumerate(output):
                        if torch.argmax(i) == y[idx]:
                            correct += 1
                        total += 1
            print("Classifier is {}% accurate".format(int(correct / total * 100)))

## Save and load a model parameters:
##torch.save(net.state_dict(), PATH)
##
##net = Net()   #TheModelClass(*args, **kwargs)
##net.load_state_dict(torch.load(PATH))
##net.eval()

