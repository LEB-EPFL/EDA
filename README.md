# adaptive-imaging
Tools for adaptive imaging in the LEB-EPFL

This project was used for the realization of adaptive temporal sampling (ATS) imaging of mitochondria and caulobacter. The two main modules are Mito2Drp1.py, NetworkWatchdog.py and NNGui.py.

The overall idea of this project is to adapt the imaging speed of a microscope to the presence of events in the images. This is achieved by implementing a feedback loop from the images taken to the microscope control. NetworkWatchdog implements part of the feedback loop, while NNGui can be used to show the resulting data. The steps of the Feedback loop are:
* Micro-Manager saves the images to a network location
* The files are detected by NetworkWatchdog
* NetworkWatchdog computes a decision parameter
* A binary file with this information is written to the network location
* The Matlab program controlling the microscope reads that data

This will result in data with different framerates, which makes for an interesting problem for actually displaying the data. Hence NNGui.

As of 16.04.2021 this is still work in progress. The goal is to get the feedback loop closer to the actual microscope, by implementing the microscope control directly in python.

Some of the important settings are in ATS_settings.json. This was used to synchronize settings on different machines that were used to run the different files.

## Mito2Drp1
Module that is used to generate the models used by ATS. The training data is data of mitochondria and Drp1 from a SIM microscope. The ground truth is a map of division events generated by Dora Mahecic using a Hessian filter on the mitochondria data and the Drp1 data plus some manual annotaion.

## NetworkWatchdog
This module looks for new files in a network location. If the files are tif files saved from Micro-Manager, the files will be prepared for the neural network. The neural network gives a heatmap of possible events in the data and the maximum of that value is saved to the binary file.

## NNGui
NNGui provides a GUI to look at the data produced by ATS. It loads a .h5 keras model for inference on the provided images. The images can be tif stacks or folders with the corresponding images in it. Especially images in folders are expected to have Micro-Manager like filenames (img_channel000_position000_time000000000_z000.tif). Stacks are usually interleaved with the two channels that the network takes.

The GUI displays both the original images and the images how they have been prepared for the network. Additionally there is a view for the heatmap produced by the neural network and a plot to show the data and framerates. Views can be hidden to enhance performance and the order in which the data is present in the images can be chosen.

## ATSSim
Module to simulate the behavior of ATS imaging on data taken at a fixed framerate.




...