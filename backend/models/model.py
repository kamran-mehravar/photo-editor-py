import torch
import torch.nn as nn
import torch.nn.functional as F


class ColorAdjustmentModel(nn.Module):
    def __init__(self):
        super(ColorAdjustmentModel, self).__init__()
        # First convolution: expects 64 filters
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        # Second convolution: expects 128 filters
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        # Fully connected layers: input size 128*32*32 = 131072, output 256, then 3
        self.fc1 = nn.Linear(128 * 32 * 32, 256)
        self.fc2 = nn.Linear(256, 3)

    def forward(self, image, params):
        # image: [batch, 3, 32, 32]
        x = F.relu(self.conv1(image))
        x = F.relu(self.conv2(x))
        x = x.view(x.size(0), -1)  # Flatten, expected shape: [batch, 128*32*32]
        x = F.relu(self.fc1(x))
        adjustments = self.fc2(x)  # Shape: [batch, 3]
        adjustments = adjustments.view(-1, 3, 1, 1)
        adjusted_image = image + params * adjustments
        return torch.clamp(adjusted_image, 0, 1)
