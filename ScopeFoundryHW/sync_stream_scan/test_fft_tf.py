import numpy as np
import tensorflow as tf
from matplotlib import pyplot as plt

# sess=tf.Session()
# # 
# # with sess.as_default()
# 
# a = tf.constant(3.0, dtype=tf.float32)
# b = tf.constant(4.0) # also tf.float32 implicitly
# total = a + b
# print(a)
# print(b)
# print(total)
# 
# print(total.eval(session = sess))


print('tf:',tf.__version__)

# 
# 
# 
sess= tf.Session()
 
 
 
# check if np.fft2d of TF.fft2d and NP have the same result
 
testimage = np.random.rand(256,)
testimage = testimage+0j
 
# ft_testimage = np.fft.fft2(testimage)
# np_result = np.sum(ft_testimage)
# print(np_result)


testimageTF = tf.Variable(testimage, dtype = tf.complex64)

#ft_testimageTF = tf.Variable(tf.complex64) 
  
ft_testimageTF = tf.fft(testimageTF)
 
print(sess.run(ft_testimageTF))
 
#tf_result = np.sum(ft_testimageTF.eval(session=sess))
#print(tf_result)
# 
# result_div = np.abs(tf_ft_testimage.eval(session=sess))
# 
# plt.imshow(np.log(result_div))
# 
# print(np_result)
# (56368.5840888+9.09494701773e-13j)
# 
# print(tf_result)
# (56368.6+0.00390625j)
