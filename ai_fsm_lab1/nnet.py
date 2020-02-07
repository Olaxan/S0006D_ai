# pip3 install torch torchvision
# pip3 install pytmx
# pip3 install pygame

import torch
import torchvision
from torchvision import transforms, datasets
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset
import torch.optim as optim
import random
import pytmx
from world import World
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
        success, path, costs = Path.plan(self.world.map, p1, p2)
        cost = 0
        if success:
            for node in path:
                cost += costs[node]

        return path, cost #y??

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

class TrainingData:

    def __init__(self, train_batch=100, test_batch=10, iterations=200, epoch_range=10):
        self.train_batch = train_batch
        self.test_batch = test_batch
        self.iterations = iterations
        self.epoch_range = epoch_range

class Net(nn.Module):

    def __init__(self, width, height):
        super().__init__()
        self.fc1 = nn.Linear(width * height, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 64)
        self.fc4 = nn.Linear(64, 100)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return F.log_softmax(x, dim=1)

    def train(self, train_data, test_data, settings: TrainingData):

        trainset = torch.utils.data.DataLoader(train_data, settings.train_batch, shuffle=True)
        testset = torch.utils.data.DataLoader(test_data, settings.test_batch, shuffle=False)
        loss_function = torch.nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.parameters(), lr=0.001)

        #Teach the NN
        for datasets in range(settings.iterations):     #10000
            for epoch in range(settings.epoch_range):   # 3 full passes over the data
                for data in trainset:                   # 'data' is a batch of data
                    X, y = data                         # X is the batch of features, y is the batch of targets.
                    self.zero_grad()                    # sets gradients to 0 before loss calc. You will do this likely every step.
                    output = self(X.view(-1, 784))      # pass in the reshaped batch (recall they are 28x28 atm)
                    loss = F.nll_loss(output, y)        # calc and grab the loss value
                    loss.backward()                     # apply this loss backwards thru the network's parameters
                    optimizer.step()                    # attempt to optimize weights to account for loss/gradients


    # Test the NN
    net.eval() # needed?
    correct = 0
    total = 0
    with torch.no_grad():
        for data in testset:
            X, y = data
            output = net(X.view(-1,784))
            #print(output)
            for idx, i in enumerate(output):
                print(torch.argmax(i), y[idx])
                if torch.argmax(i) == y[idx]:
                    correct += 1
                total += 1

print("Accuracy: ", round((correct/total)*100, 3))

## Save and load a model parameters:
##torch.save(net.state_dict(), PATH)
##
##net = Net()   #TheModelClass(*args, **kwargs)
##net.load_state_dict(torch.load(PATH))
##net.eval()

