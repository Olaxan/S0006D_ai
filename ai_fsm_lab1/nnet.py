import os.path as io
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset
from tqdm import tqdm
from path import Path


class PathDataset(Dataset):
    # A pytorch dataset class for holding data for a text classification task.

    def __init__(self, world, data_points, heuristic=None):
        self.world = world
        self.X, self.y = self.populate_dataset(data_points, heuristic)

    def random_path(self, heuristic):
        """Get a random A-star path in the world"""

        p1 = self.world.get_random_cell()
        p2 = self.world.get_random_cell()
        success, path, cost = Path.a_star_search(self.world.graph, p1, p2, heuristic)
        grid = [[0 for col in range(self.world.width)] for row in range(self.world.height)]
        grid[p1[0]][p1[1]] = 1
        grid[p2[0]][p2[1]] = 1

        return grid, cost #y??

    def populate_dataset(self, count, heuristic):
        """Fill the dataset with random paths for training purposes"""

        x = []
        y = []
        for i in tqdm(range(count)):
            a, b = self.random_path(heuristic)
            x.append(a)
            y.append(b)
        return x, y

    @property
    def input(self):
        return self.world.width * self.world.height

    @property
    def labels(self):
        return max(self.y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return torch.Tensor(self.X[idx]), self.y[idx]

class Net(nn.Module):

    def __init__(self, input_size, output_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 120)
        self.fc3 = nn.Linear(120, 64)
        self.fc4 = nn.Linear(64, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        return F.log_softmax(x, dim=1)

    @property
    def input(self):
        return self.fc1.in_features

    @property
    def output(self):
        return self.fc4.out_features

class TrainingData:

    def __init__(self, epochs=1000, set_size=200, train_batch=200, test_batch=10):
        self.epochs = epochs
        self.set_size = set_size
        self.train_batch = train_batch
        self.test_batch = test_batch

class NeuralHeuristic:

    def __init__(self, world, file_path=None, training_data: TrainingData = None):
        self.world = world
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        if io.exists(file_path):
            self.load(file_path)
        elif training_data is not None:
            self.train(training_data)

        self.net.to(self.device)
        self.net.eval()

    def train(self, data):

        heuristic = self.world.heuristic

        print("Generating training data...")
        train_data = PathDataset(self.world, data.set_size, heuristic)
        print("Generating test data...")
        test_data = PathDataset(self.world, data.set_size, heuristic)
        train_set = torch.utils.data.DataLoader(train_data, data.train_batch, shuffle=True)
        test_set = torch.utils.data.DataLoader(test_data, data.test_batch, shuffle=False)

        assert train_data.input == test_data.input, "Input data mismatch!"

        self.net = Net(train_data.input, max(train_data.labels, test_data.labels) + 1)
        loss_function = torch.nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.net.parameters(), lr=0.001)

        print('Training net on {}'.format(self.device))

        self.net = self.net.to(self.device)

        estimate = 0
        correct = 0
        for epoch in tqdm(range(data.epochs)):
            for data in train_set:      # 'data' is a batch of data
                X, y = data             # X is the batch of features, y is the batch of targets
                self.net.zero_grad()    # sets gradients to 0 before loss calc
                X = X.to(self.device)
                output = self.net(X.view(-1, self.net.input))      # pass in the reshaped batch
                output = output.cpu()
                loss = loss_function(output, y)     # calc and grab the loss value
                loss.backward()                     # apply this loss backwards thru the network's parameters
                optimizer.step()                    # attempt to optimize weights to account for loss/gradients
            self.net = self.net.to(self.device)
            with torch.no_grad():
                for data in test_set:
                    X, y = data
                    X = X.to(self.device)
                    output = self.net(X.view(-1, self.net.input))
                    output = output.cpu()
                    for idx, i in enumerate(output):
                        correct += int(y[idx])
                        estimate += int(torch.argmax(i))

        error = 1 - (abs(estimate - correct) / correct)
        print("Classifier is {}% accurate".format(int(error * 100)))

    def save(self, path):
        torch.save({
            'model_dict':self.net.state_dict(),
            'model_in':self.net.input,
            'model_out':self.net.output}, path)

    def load(self, path):
        checkpoint = torch.load(path)
        in_size = checkpoint['model_in']
        out_size = checkpoint['model_out']
        self.net = Net(in_size, out_size)
        self.net.load_state_dict(checkpoint['model_dict'])

    def __call__(self, start, goal):
        p1 = start
        p2 = goal
        grid = [[0 for col in range(self.world.width)] for row in range(self.world.height)]
        grid[p1[0]][p1[1]] = 1
        grid[p2[0]][p2[1]] = 1
        X = torch.Tensor(grid)
        X = X.to(self.device)
        output = self.net(X.view(-1, self.net.input))
        output = output.cpu()
        return int(torch.argmax(output))

