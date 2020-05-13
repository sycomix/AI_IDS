# First iteration of AI IDS RDP Project
# Written By Idan Tau & Shahaf Haller
# CNN module based on https://ieeexplore.ieee.org/document/8171733
# "Algorithm 1 Spatial Feature Learning" - HAST_I

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class Net(nn.Module):
    
    # Actual parameters of the CNN are not mentioned in the article,
    # but since both temp vectors are concatenated the numbers should be 
    # different so both CNN won't be symmetrical
    
    # C{i} - Num of convolution channels
    # S{i} - Size of convolution matrix
    # T{i} - size of maxPooling layer matrix
    C = np.array([6,  16,  6,  16])
    S = np.array([5,   5,  5,   5])
    T = np.array([2,   2,  2,   2])
    
    # These are changed based on how the images are made
    # from packets of data
    
    input_channels = 3
    image_dimension = 32

    def __init__(self):     
        super(Net, self).__init__()
        
        # Define the convolution functions:
        # 4 convolutions are used, 2 for each vector
        self.conv1_1 = nn.Conv2d(Net.input_channels, Net.C[0], Net.S[0])
        self.conv1_2 = nn.Conv2d(Net.C[0], Net.C[1], Net.S[1])
        self.conv2_1 = nn.Conv2d(Net.input_channels, Net.C[2], Net.S[2])
        self.conv2_2 = nn.Conv2d(Net.C[2], Net.C[3], Net.S[3])
        
        # A convolution matrix of size 5 will reduce 2 indices from each side
        conv_reduction = (Net.S - 1) / 2
        
        # First convolution reduction
        size_1 = Net.image_dimension - conv_reduction[0];
        size_2 = Net.image_dimension - conv_reduction[2];
        
        # First Max pooling reduction
        # P.S. make sure the result is even for easier living
        size_1 /= Net.T[0]
        size_2 /= Net.T[2]
        
        # Second convolution reduction
        size_1 -= conv_reduction[1]; 
        size_2 -= conv_reduction[3];
        
        # Second Max pooling reduction
        # P.S. make sure the result is even for easier living        
        size_1 /= Net.T[1]
        size_2 /= Net.T[3]
        
        # Final size for the linear vector reduction process
        size_1 *= Net.C[1]
        size_2 *= Net.C[3]

        # First linear reduction
        self.fc1_1 = nn.Linear(size_1, size_1 // 2)
        self.fc2_1 = nn.Linear(size_2, size_2 // 2)
        
        # Second linear reduction
        self.fc1_2 = nn.Linear(size_1 // 2, size_1 // 4)
        self.fc2_2 = nn.Linear(size_2 // 2, size_2 // 4)

        # Final linear reduction reduces us to a [false, positive] vector
        self.fc1_3 = nn.Linear(size_1 // 4, 2)
        self.fc2_3 = nn.Linear(size_2 // 4, 2)

    def forward(self, z):
        
        # relu(x) -> max{x,0}
        
        # Conv -> relu -> pool -> conv -> relu -> pool
        x = F.max_pool2d(F.relu(self.conv1_1(z)), Net.T[0])
        x = F.max_pool2d(F.relu(self.conv1_2(x)), Net.T[1])
    
        y = F.max_pool2d(F.relu(self.conv2_1(z)), Net.T[2])
        y = F.max_pool2d(F.relu(self.conv2_2(y)), Net.T[3])

        # Turn the matrices into long vectors
        x = x.view(1, self.num_flat_features(x))
        y = y.view(1, self.num_flat_features(y))
        
        # Reduce the vectors
        x = F.relu(self.fc1_1(x))
        x = F.relu(self.fc1_2(x))
        x = self.fc1_3(x)
        
        y = F.relu(self.fc2_1(y))
        y = F.relu(self.fc2_2(y))
        y = self.fc2_3(y)

        return x + y

    def num_flat_features(self, z):
        size = z.size()[1:]  # all dimensions except the batch dimension
        num_features = 1
        for s in size:
            num_features *= s
        return num_features


net = Net()
print(net)