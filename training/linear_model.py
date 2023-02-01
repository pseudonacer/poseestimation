# -*- coding: utf-8 -*-
"""Linear_model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CJ10oYV8j1FjWjBlanoeGoOZ1qgUDACa
"""

import tensorflow as tf

class Block(tf.keras.Model):
    def __init__(self, embed = 1024, dropout_rate = 0.3):
        super(Block, self).__init__()
        self.d1 = tf.keras.layers.Dense(embed)
        self.bn1= tf.keras.layers.BatchNormalization()
        self.ac1= tf.keras.layers.ReLU()
        self.dp1= tf.keras.layers.Dropout(dropout_rate)

    def call(self,x):
        x = self.dp1(self.ac1(self.bn1(self.d1(x))))
        return x

class OuterBlock(tf.keras.Model):
    def __init__(self,embed = 1024, dropout_rate = 0.3):
        super(OuterBlock, self).__init__()
        self.fc = tf.keras.layers.Dense(embed, name = "resize")
        self.b1 = Block(embed ,dropout_rate)
        self.b2 = Block(embed ,dropout_rate)
        
    def call(self, inputs):
        skip = self.fc(inputs)
        x = self.b1(inputs)
        x = self.b2(x)
        #x = self.add([x, skip])
        return skip + x

class OuterBlock2(tf.keras.Model):
    def __init__(self, embed = 1024, dropout_rate = 0.3):
        super(OuterBlock2,  self).__init__()
        self.b1 = OuterBlock(embed, dropout_rate)
        self.b2 = OuterBlock(embed, dropout_rate)
        self.d3 = tf.keras.layers.Dense(156)
#        self.reshape = tf.keras.layers.Reshape((1,52,3))
        
    def call(self, inputs):
        x = self.b1(inputs)
        x = self.b2(x)
        x = self.d3(x)
#        x = self.reshape(x)
        return x