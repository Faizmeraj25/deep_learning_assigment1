# pip install wandb

import numpy as np 
import pandas as pd
import math
import matplotlib.pyplot as plt
import wandb
from keras.datasets import fashion_mnist
from sklearn.model_selection import train_test_split
import tensorflow as tf
(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=0.1)

x_train = x_train / 255
x_test = x_test / 255
x_train = x_train.reshape(x_train.shape[0], -1)
x_test = x_test.reshape(x_test.shape[0], -1)
x_val = x_val.reshape(x_val.shape[0], -1)



print(x_val.shape)

class NN: 
  # instantiate the weights and biases with random numbers. 
  def __init__(self, size, wt_initialisation): 
    self.W= [] 
    self.B = [] 
    self.preactivation = []
    self.activation = []
    if wt_initialisation.lower() == "xavier":
      for i in range(1, len(size)):
        n = np.sqrt(6 / (size[i] + size[i-1]))
        w = np.random.uniform(-n , n, (size[i], size[i-1]))
        b = np.random.uniform(-n , n, (size[i])) 
        self.W.append(w)
        self.B.append(b)
    # Random Initialisation
    else: 
      for i in range(1, len(size)):
        w = np.random.rand(size[i], size[i-1]) /(np.sqrt(size[i]))
        b = np.random.rand(size[i]) 
        self.W.append(w)
        self.B.append(b)


###############################################################
  def normalize(self, x):
    for i in range(x.shape[0]):
      argmax = np.argmax(x[i])
      maxval = x[i][argmax]
      x[i] = (x[i])/(maxval)
    return x
###############################################################

  def sigmoid(self, x): 
    return 1/(1 + np.exp(-x))

###############################################################

  def sigmoid_derivative(self, x):
    sig = self.sigmoid(x)
    return sig*(1-sig)

###############################################################

  def relu(self, x): 
    return np.maximum(0, x)

###############################################################

  def relu_derivative(self, x):
    return np.max(np.sign(x),0)


###############################################################
    
  def tanh(self, x): 
    return np.tanh(x)

###############################################################

  def tanh_derivative(self, x):
    t = np.tanh(x)
    return 1 - t*t

###############################################################

  def softmax(self, x):
    for i in range(x.shape[0]):
      sum=0
      for j in range(x.shape[1]):
        sum=sum+np.exp(x[i][j])
      x[i]=np.exp(x[i])/sum
    return x

###############################################################

  def one_hot_encoded(self, y, no_of_classes):
    return np.eye(no_of_classes)[y]

###############################################################

  def cross_entropy(self, y_train, y_hat):
    loss=0
    for i in range (y_hat.shape[0]):
      loss+=-(np.log2(y_hat[i][y_train[i]]))
    return loss/y_hat.shape[0]


###############################################################


  def squared_error(self, y_train, y_hat, no_of_classes):
        loss = 0
        y_onehot = self.one_hot_encoded(y_train, no_of_classes)
        for i in range(y_hat.shape[0]):
            loss += np.sum((y_hat[i] - y_onehot[i])**2)
        return loss / y_train.shape[0]


###############################################################

  def hadmard_mul(self, a, b):
    c = np.array(np.zeros((a.shape[0],a.shape[1])))
    for i in range(a.shape[0]):
      for j in range(a.shape[1]):
        c[i][j] = a[i][j] * b[i][j]
    return c

###############################################################


    def l2_regularize(self, lambd, batch_size):
        acc = 0
        for i in range(len(self.W)):
            acc += np.sum(self.W[i] ** 2)
        return (lambd * acc)/2


###############################################################
  def batch_converter(self, x, y, batch_size):
    no_datapoints = x.shape[0]
    no_batches = no_datapoints // batch_size
    x_batch = []
    y_batch = []
    for i in range(no_batches):
      s = i*batch_size
      e = min((i+1)*batch_size , x.shape[0])
      x1 = np.array(x[s:e])
      y1 = np.array(y[s:e])
      x_batch.append(x1)
      y_batch.append(y1)
    # jo datapoints last me bach jayenge wo yaha pe add kr rhe
    if no_batches * batch_size < x_train.shape[0]:
      x1 = np.array(x_train[no_batches* batch_size :])
      y1 = np.array(y_train[no_batches* batch_size :])
      x_batch.append(x1)
      y_batch.append(y1)
    return x_batch, y_batch


###############################################################

  def forward(self, input, size, activation_function = "sigmoid"):
    # Calculating for the hiddlen layers
    for i in range(len(size)-2):
      Y = np.dot(input, self.W[i].T)   + self.B[i]
      if i == 0 and activation_function.lower() == "relu":
        Y= self.normalize(Y)
      elif activation_function.lower() == "tanh":
        Y = self.normalize(Y)
      if i < len(self.preactivation):
        self.preactivation[i] = Y
      else:
        self.preactivation.append(Y)
      # Y_dash = self.normalize(Y)
      if activation_function.lower() == "relu":
        Z = self.relu(Y)
      elif activation_function.lower() =="sigmoid":
        Z = self.sigmoid(Y)
      elif activation_function.lower() =="tanh":
        Z = self.tanh(Y)
      else:
        print("NO ACTIVATION FUNCTION SELECTED")

      if i < len(self.activation):
        self.activation[i] = Z
      else:
        self.activation.append(Z)
      input = Z
    #Calculating for the output layer.
    i =  len(size)-2
    Y = np.dot(input, self.W[i].T) + self.B[i]
    # Y = self.normalize(Y)
    if i < len(self.preactivation):
        self.preactivation[i] = Y
    else:
      self.preactivation.append(Y)
    Z = self.softmax(Y)
    if i < len(self.activation):
        self.activation[i] = Z
    else:
        self.activation.append(Z)
    return self.preactivation, self.activation

###############################################################


  def backward(self, layers, x, y ,no_of_classes, preac, ac, activation_function="sigmoid"):
    no_layers = len(layers)
    grad_a = [] 
    grad_w = []
    grad_b = []
    grad_h = []
    y_onehot = self.one_hot_encoded(y, no_of_classes)
    grad_a.append(-(y_onehot - ac[len(ac)-1]))

    for i in range(no_layers-2, -1, -1):
      if i == 0:
        dw = (grad_a[no_layers-2-i].T @ x) #/ y.shape[0]
        db = np.sum(grad_a[no_layers-2-i],axis=0)/y.shape[0]
      else: 
        dw = (grad_a[no_layers-2-i].T @ ac[i-1])#/ y.shape[0]
        db = np.sum(grad_a[no_layers-2-i],axis=0)/ y.shape[0]
        dh_1 = grad_a[no_layers-2-i] @ self.W[i]
        sig = 0 
        if activation_function.lower() == "sigmoid":
          sig = self.sigmoid_derivative(preac[i-1])
        elif activation_function.lower() == "relu":
          sig = self.relu_derivative(preac[i-1])
        elif activation_function.lower() == "tanh":
          sig = self.tanh_derivative(preac[i-1])
        else:
          print("CANNOT UPDATE WEIGHT AND BIASES !!")

        da_1 = dh_1 * sig

        grad_h.append(dh_1)
        grad_a.append(da_1)
      grad_w.append(dw)
      grad_b.append(db)
    return grad_w, grad_b


###############################################################


  def gradient_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, eta, epochs, loss_func, lambd, plot_conf_mat):
    l = len(layers)
    loss_arr = []
    for ep in range(epochs):
      preac, ac = self.forward(x_train, layers, activation_function)
      grad_w, grad_b = self.backward(layers, x_train, y_train, no_of_classes, preac, ac, activation_function)

      for i in range(l-1):
        self.W[i] += -(eta * grad_w[l-i-2] + (eta * lambd * self.W[i])/self.W[i].shape[0])
        self.B[i] += -eta * grad_b[l-i-2]
      # print(ac[len(ac)-1])
      # preac, ac = self.forward(x, layers)
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")

      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)


###############################################################


  def batch_grad_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, eta, batch_size, n_iterations, loss_func, lambd, plot_conf_mat):
    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    loss_arr = []
    for i in range(n_iterations):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes,preac, ac, activation_function)
        length = len(layers)
        for l in range(length-1):
          # print("shape",self.W[l].shape, grad_w[length-l-2].shape)
          self.W[l] += -(eta * grad_w[length-l-2] + (eta * lambd * self.W[i])/self.W[i].shape[0])
          self.B[l] += -eta * grad_b[length-l-2]
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)
      
      loss_train += l2_regularize(lambd, xb.shape[0])
      loss_val += l2_regularize(lambd, xb.shape[0])
      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", i+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", i+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", i+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", i+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)


###############################################################


  def momentum_grad_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, batch_size, eta, epochs, beta, loss_func,lambd, plot_conf_mat):
    l = len(layers)
    prev_w = [] 
    prev_b = [] 
    loss_arr = []
    for i in range(l-1):
      prev_w.append(np.zeros(self.W[i].shape))
      prev_b.append(np.zeros(self.B[i].shape))

    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    for ep in range(epochs):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes, preac, ac, activation_function)
        for i in range(l-1):
          prev_w[i] = beta*prev_w[i] + grad_w[l-i-2]
          prev_b[i] = beta*prev_b[i] + grad_b[l-i-2]
          self.W[i] += -eta*prev_w[i]
          self.B[i] += -eta*prev_b[i]
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)


###############################################################

  def nesterov_gradient_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, batch_size, eta, epochs, beta, loss_func,lambd, plot_conf_mat):
    l = len(layers)
    prev_w = []
    prev_b = []
    loss_arr = []
    for i in range(l-1):
      prev_w.append(np.zeros(self.W[i].shape))
      prev_b.append(np.zeros(self.B[i].shape))

    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    
    for ep in range(epochs):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        # print("y_hat", ac[len(ac)-1])
        for i in range(l-1):
          self.W[i] += -beta * prev_w[i]
          self.B[i] += -beta * prev_b[i]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes, preac, ac, activation_function)
        # print("grad_w", grad_w)
        for i in range(l-1):
          prev_w[i] = beta * prev_w[i] + grad_w[l-i-2]
          prev_b[i] = beta * prev_b[i] + grad_b[l-i-2]
          self.W[i] += -eta * prev_w[i]
          self.B[i] += -eta * prev_b[i]
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)



###############################################################


  def rmsprop_gradient_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, batch_size, eta, epochs, beta, loss_func,lambd, plot_conf_mat):
    l = len(layers)
    vw = []
    vb = []
    loss_arr = []
    eps = 1e-4
    for i in range(l-1):
      vw.append(np.zeros(self.W[i].shape))
      vb.append(np.zeros(self.B[i].shape))

    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    for ep in range(epochs):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes, preac, ac, activation_function)
        for i in range(l-1):
          vw[i] = beta * vw[i] + (1-beta) * grad_w[l-i-2] * grad_w[l-i-2]
          vb[i] = beta * vb[i] + (1-beta) * grad_b[l-i-2] * grad_b[l-i-2]
          self.W[i] =  self.W[i] - (eta * grad_w[l-i-2])/np.sqrt(vw[i] + eps)
          self.B[i] =  self.B[i] - (eta * grad_b[l-i-2])/np.sqrt(vb[i] + eps)
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)

###############################################################


  def adam_gradient_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, batch_size, eta, epochs, beta1, beta2, loss_func,lambd, plot_conf_mat):
    l = len(layers)
    mw = []
    mb = []
    vw = []
    vb = []
    loss_arr = []
    eps = 1e-10
    for i in range(l-1):
      vw.append(np.zeros(self.W[i].shape))
      vb.append(np.zeros(self.B[i].shape))
      mw.append(np.zeros(self.W[i].shape))
      mb.append(np.zeros(self.B[i].shape))
    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    for ep in range(epochs):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes, preac, ac, activation_function)
        for i in range(l-1):
          mw[i] = beta1 * mw[i] + (1-beta1) * grad_w[l-i-2]
          mb[i] = beta1 * mb[i] + (1-beta1) * grad_b[l-i-2]
          mw_hat = mw[i] / (1 - np.power(beta1, j+1))
          mb_hat = mb[i] / (1 - np.power(beta1, j+1))

          vw[i] = beta2 * vw[i] + (1-beta2) * grad_w[l-i-2] * grad_w[l-i-2]
          vb[i] = beta2 * vb[i] + (1-beta2) * grad_b[l-i-2] * grad_b[l-i-2]
          vw_hat = vw[i] / (1 - np.power(beta2, j+1))
          vb_hat = vb[i] / (1 - np.power(beta2, j+1))

          self.W[i] = self.W[i] - (eta * mw_hat)/(np.sqrt(vw_hat) + eps)
          self.B[i] = self.B[i] - (eta * mb_hat)/(np.sqrt(vb_hat) + eps)
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)

###############################################################


  def nadam_gradient_descent(self, x_train, y_train, x_test, y_test, no_of_classes, layers, activation_function, batch_size, eta, epochs, beta1, beta2, loss_func,lambd, plot_conf_mat):
    l = len(layers)
    mw = []
    mb = []
    vw = []
    vb = []
    loss_arr = []
    eps = 1e-10
    for i in range(l-1):
      vw.append(np.zeros(self.W[i].shape))
      vb.append(np.zeros(self.B[i].shape))
      mw.append(np.zeros(self.W[i].shape))
      mb.append(np.zeros(self.B[i].shape))
    x_batch, y_batch = self.batch_converter(x_train, y_train, batch_size)
    for ep in range(epochs):
      for j in range(len(x_batch)):
        xb = x_batch[j]
        yb = y_batch[j]
        preac, ac = self.forward(xb, layers, activation_function)
        grad_w, grad_b = self.backward(layers, xb, yb, no_of_classes, preac, ac, activation_function)
        for i in range(l-1): 
          mw[i] = beta1 * mw[i] + (1-beta1)* grad_w[l-i-2]
          mb[i] = beta1 * mb[i] + (1-beta1)* grad_b[l-i-2]
          mw_hat = mw[i] / (1 - np.power(beta1, j+1))
          mb_hat = mb[i] / (1 - np.power(beta1, j+1))

          vw[i] = beta2 * vw[i] + (1-beta2) * grad_w[l-i-2] * grad_w[l-i-2]
          vb[i] = beta2 * vb[i] + (1-beta2) * grad_b[l-i-2] * grad_b[l-i-2]
          vw_hat = vw[i] / (1 - np.power(beta2, j+1))
          vb_hat = vb[i] / (1 - np.power(beta2, j+1))

          self.W[i] = self.W[i] - (eta/(np.sqrt(vw[i]) + eps)) * (beta1 * mw_hat + (((1-beta1) * grad_w[l-i-2]) / (1 - np.power(beta1, j+1))))
          self.B[i] = self.B[i] - (eta/(np.sqrt(vb[i]) + eps)) * (beta1 * mb_hat + (((1-beta1) * grad_b[l-i-2]) / (1 - np.power(beta1, j+1))))
      preac, ac = self.forward(x_train, layers)
      if loss_func.lower() == "crossentropy":
        loss_train = self.cross_entropy(y_train, ac[len(ac)-1])
      else:
        loss_train = self.squared_error(y_train, ac[len(ac)-1], no_of_classes)
      preac, ac = self.forward(x_test, layers)
      if loss_func.lower() == "crossentropy":
        loss_val = self.cross_entropy(y_test, ac[len(ac)-1])
      else: 
        loss_val = self.squared_error(y_test, ac[len(ac)-1], no_of_classes)


      loss_arr.append(loss_val)
      accur_train = self.test_accuracy(layers, x_train, y_train, activation_function)
      accur_val = self.test_accuracy(layers, x_test, y_test, activation_function)
      print("Iteration No : \t\t", ep+1, "\t Train Loss\t\t", loss_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Loss\t\t", loss_val)
      print("\n")
      print("Iteration No : \t\t", ep+1, "\t Train Accuracy\t\t", accur_train)
      print("Iteration No : \t\t", ep+1, "\t Validate Accuracy\t\t", accur_val)
      print("---------------------------------------------------------")
      wandb.log({"train_accuracy":accur_train,"train_error":loss_train,"val_accuracy":accur_val,"val_error":loss_val})
    if plot_conf_mat == True: 
      y_pred = ac[len(ac)-1]
      y_pred = np.argmax(y_pred, axis = 1)
      self.Confunsion_Matrix_Plot(y_pred, y_test)
    
###############################################################

  def test_accuracy(self, layers, x, y, activation_function):
    preac, ac = self.forward(x, layers, activation_function)
    y_pred = ac[len(ac)-1]
    err_count = 0
    for i in range(y_pred.shape[0]):
      maxval = -(math.inf)
      maxind= -1
      for j in range(y_pred.shape[1]): 
        if maxval < y_pred[i][j]:
          maxval = y_pred[i][j]
          maxind = j
      if maxind != y[i]:
        err_count = err_count + 1
    return ((y.shape[0] - err_count)/y.shape[0])*100
      
###############################################################
  def PlotError(self, ErrorSum):
    Iter = [] 
    for i in range(len(ErrorSum)):
      Iter.append(i)
    plt.plot(Iter,ErrorSum)
    plt.title('Error v/s Iteration')
    plt.xlabel('No of Iterations')
    plt.ylabel('Error')
    plt.show()
###############################################################

  def Confunsion_Matrix_Plot(self, y_pred, y):
    class_names = ['T-shirt/top', 'Trouser', 'Pullover', 'Dress', 'Coat', 'Sandal', 'Shirt', 'Sneaker', 'Bag', 'Ankle boot']
    wandb.log({"Confunsion_Matrix_Plot ": wandb.plot.confusion_matrix(probs = None, y_true = y, preds = y_pred, class_names = class_names)})
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_pred, y)
    print(cm)

def main(x_train, y_train, x_val, y_val, input_size, no_hidden_layers, hidden_layer_size, no_of_classes, wt_initialisation, optimiser, activation_function, batch_size, eta, epoch,beta, beta1, beta2, loss_func, lambd, plot_conf_mat):
  layers = []
  layers.append(input_size)
  for i in range(no_hidden_layers):
    layers.append(hidden_layer_size)
  layers.append(no_of_classes)
    
  nn = NN(layers, wt_initialisation)

  if optimiser.lower() == "bgd":
    nn.batch_grad_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, eta, batch_size, epoch, loss_func, lambd, plot_conf_mat)
  elif optimiser.lower() == "vanillagd":
    nn.gradient_descent(x_train, y_train,x_val, y_val, no_of_classes, layers, activation_function, eta, epoch, loss_func, lambd, plot_conf_mat)
  elif optimiser.lower() == "mgd":
    nn.momentum_grad_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, batch_size, eta, epoch, beta, loss_func, lambd, plot_conf_mat)
  elif optimiser.lower() == "ngd":
    nn.nesterov_gradient_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, batch_size, eta, epoch, beta, loss_func, lambd, plot_conf_mat)

  elif optimiser.lower() == "rmsprop":
    nn.rmsprop_gradient_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, batch_size, eta, epoch, beta, loss_func, lambd, plot_conf_mat)
    
  elif optimiser.lower() == "adam":
    nn.adam_gradient_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, batch_size, eta, epoch, beta1, beta2, loss_func, lambd, plot_conf_mat)

  elif optimiser.lower() == "nadam":
    nn.nadam_gradient_descent(x_train, y_train, x_val, y_val, no_of_classes, layers, activation_function, batch_size, eta, epoch, beta1, beta2, loss_func, lambd,plot_conf_mat)


default_params=dict(
epochs=3,
batch_size=32,
input_size = 784,
optimizer='nadam',
learning_rate=0.001,
loss_func = "crossentropy",
activation_function='sigmoid',
no_of_classes = 10,
no_of_hidden_layers=3,
hidden_layer_size=128,
wt_initialisation='Xavier',
plot_conf_mat = True,
lambd = 0, 
)
#Global Variables
beta = 0.9
beta1 = 0.9
beta2 = 0.999


run=wandb.init(config=default_params,project='DeepLearning_Assignment1',entity='cs22m081',reinit='true')
config=wandb.config
run.name = "Plot Confusion Matrix"

epochs=config.epochs
batch_size=config.batch_size
optimizer=config.optimizer
learning_rate = config.learning_rate
loss_func = config.loss_func
no_of_hidden_layers=config.no_of_hidden_layers
hidden_layer_size=config.hidden_layer_size
wt_initialisation=config.wt_initialisation
input_size=config.input_size
activation_function = config.activation_function
no_of_classes = config.no_of_classes
lambd = config.lambd
plot_conf_mat = config.plot_conf_mat

main(x_train, y_train, x_val, y_val, input_size, no_of_hidden_layers, hidden_layer_size, no_of_classes, wt_initialisation, optimizer, activation_function, batch_size, learning_rate, epochs, beta, beta1, beta2, loss_func,lambd, plot_conf_mat)
  