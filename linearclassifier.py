"""
Functions for training and predicting with linear classifiers
"""
import numpy as np
import pylab as plt
from scipy.optimize import minimize, check_grad


def linear_predict(data, model):
    """
    Predicts a multi-class output based on scores from linear combinations of features. 
    
    :param data: size (d, n) ndarray containing n examples described by d features each
    :type data: ndarray
    :param model: dictionary containing 'weights' key. The value for the 'weights' key is a size 
                    (d, num_classes) ndarray
    :type model: dict
    :return: length n vector of class predictions
    :rtype: array
    """

    # This function does the prediction by doing matrix multiplication
    # Transpose(weight matrix) x data

    return np.argmax(np.matmul(model['weights'].T,data), axis=0)
    

def perceptron_update(data, model, label):
    """
    Update the model based on the perceptron update rules and return whether the perceptron was correct
    
    :param data: (d, 1) ndarray representing one example input
    :type data: ndarray
    :param model: dictionary containing 'weights' key. The value for the 'weights' key is a size 
                    (d, num_classes) ndarray
    :type model: dict
    :param label: the class label of the single example
    :type label: int
    :return: whether the perceptron correctly predicted the provided true label of the example
    :rtype: bool
    """

    # Get prediction by multiplying weights with transpose of data
    idx_pred = np.argmax(np.matmul(model['weights'].T,data),axis=0)

    # Update the weights if the predicted value is not same as the label class
    if idx_pred!=label:

        model['weights'][:, label] = model['weights'][:, label] + data
        model['weights'][:, idx_pred] = model['weights'][:, idx_pred] - data
        return False
    
    return True


def log_reg_train(data, labels, params, model=None, check_gradient=False):
    """
    Train a linear classifier by maximizing the logistic likelihood (minimizing the negative log logistic likelihood)
     
    :param data: size (d, n) ndarray containing n examples described by d features each
    :type data: ndarray
    :param labels: length n array of the integer class labels 
    :type labels: array
    :param params: dictionary containing 'lambda' key. Lambda is the regularization parameter and it should be a float
    :type params: dict
    :param model: dictionary containing 'weights' key. The value for the 'weights' key is a size 
                    (d, num_classes) ndarray
    :type model: dict
    :param check_gradient: Boolean value indicating whether to run the numerical gradient check, which will skip
                            learning after checking the gradient on the initial model weights.
    :type check_gradient: Boolean
    :return: the learned model 
    :rtype: dict
    """
    d, n = data.shape
    num_classes = np.unique(labels).size

    if model:
        weights = model['weights'].ravel()
    else:
        weights = np.zeros(d * num_classes)

    def log_reg_nll(new_weights):
        """
        This internal function returns the negative log-likelihood (nll) of the data given the logistic regression weights
        
        :param new_weights: weights to use for computing logistic regression likelihood
        :type new_weights: ndarray
        :return: tuple containing (<negative log likelihood of data>, gradient)
        :rtype: tuple
        """
        # reshape the weights, which the optimizer prefers to be a vector, to the more convenient matrix form
        new_weights = new_weights.reshape((d, num_classes))

        lambda_val = params['lambda']
        new_weights_t = new_weights.transpose()
        wt = np.dot(new_weights_t, data)
        le = logsumexp(wt, 0)[0]
        
        nll_val = 0
        
        for i in range(n):
            nll_val += np.dot(new_weights[:, labels[i]], data[:,i])
        
        nll =  np.sum((lambda_val * (new_weights * new_weights))/2) + le.sum() - nll_val

        gradient = lambda_val * new_weights

        for c in range(num_classes):
            exp_p = np.exp(wt[c,:] - le)
            log_p = np.tile(exp_p, (d, 1))
            gradient[:, c] += np.multiply(log_p, data).sum(axis=1)
            for i in range(n):
                if labels[i] == c:
                    gradient[:, c] -= data[:, i]

        return nll, gradient

    if check_gradient:
        grad_error = check_grad(lambda w: log_reg_nll(w)[0], lambda w: log_reg_nll(w)[1].ravel(), weights)
        print("Provided gradient differed from numerical approximation by %e (should be around 1e-3 or less)" % grad_error)
        return model

    # pass the internal objective function into the optimizer
    res = minimize(lambda w: log_reg_nll(w)[0], jac=lambda w: log_reg_nll(w)[1].ravel(), x0=weights)
    weights = res.x

    model = {'weights': weights.reshape((d, num_classes))}

    return model


def plot_predictions(data, labels, predictions):
    """
    Utility function to visualize 2d, 4-class data 
    
    :param data: 
    :type data: 
    :param labels: 
    :type labels: 
    :param predictions: 
    :type predictions: 
    :return: 
    :rtype: 
    """
    num_classes = np.unique(labels).size

    markers = ['x', 'o', '*',  'd']

    for i in range(num_classes):
        plt.plot(data[0, np.logical_and(labels == i, labels == predictions)],
                 data[1, np.logical_and(labels == i, labels == predictions)],
                 markers[i] + 'g')
        plt.plot(data[0, np.logical_and(labels == i, labels != predictions)],
                 data[1, np.logical_and(labels == i, labels != predictions)],
                 markers[i] + 'r')


def logsumexp(matrix, dim=None):
    """
    Compute log(sum(exp(matrix), dim)) in a numerically stable way.
    
    :param matrix: input ndarray
    :type matrix: ndarray
    :param dim: integer indicating which dimension to sum along
    :type dim: int
    :return: numerically stable equivalent of np.log(np.sum(np.exp(matrix), dim)))
    :rtype: ndarray
    """
    try:
        with np.errstate(over='raise', under='raise'):
            return np.log(np.sum(np.exp(matrix), dim, keepdims=True))
    except:
        max_val = np.nan_to_num(matrix.max(axis=dim, keepdims=True))
        with np.errstate(under='ignore', divide='ignore'):
            return np.log(np.sum(np.exp(matrix - max_val), dim, keepdims=True)) + max_val